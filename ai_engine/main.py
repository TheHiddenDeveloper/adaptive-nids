#!/usr/bin/env python3
"""
Service 2: AI Learning Engine (FIXED: supports fractional hours)
- Consumes flows from Redis Streams
- Performs UNSUPERVISED baseline learning (7-14 days)
- Deploys adaptive models to /models/latest
"""
import os
import sys
import time
import json
import signal
import numpy as np
import redis
from datetime import datetime, timedelta
from typing import List
import logging

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from ai_engine.baseline_learner import BaselineLearner
from ai_engine.model_registry import ModelRegistry
from shared.features import CIC_FEATURES

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AILearningEngine")

class AILearningEngine:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD", None),
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.stream_key = "nids:flows:stream"
        self.last_id = "0-0"
        
        # FIX: Handle fractional hours correctly (e.g., "0.01" = 36 seconds)
        baseline_hours_str = os.getenv("BASELINE_HOURS", "168")  # 7 days default
        try:
            self.baseline_hours = float(baseline_hours_str)
        except ValueError:
            logger.warning(f"Invalid BASELINE_HOURS '{baseline_hours_str}', defaulting to 168 hours (7 days)")
            self.baseline_hours = 168.0
        
        self.baseline_end = None
        self.state = "BASELINE_LEARNING"
        self.baseline_flows: List[np.ndarray] = []
        self.model_registry = ModelRegistry(os.getenv("MODEL_DIR", "/models"))
        self.learner = None
        self.running = True
        
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
        
        logger.info("Intialized AI Learning Engine")
        logger.info(f"  Redis stream: {self.stream_key}")
        logger.info(f"  Baseline period: {self.baseline_hours} hours ({self.baseline_hours/24:.2f} days)")

    def shutdown(self, signum, frame):
        logger.info("🛑 Shutdown requested")
        self.running = False

    def consume_flows(self, count: int = 1000) -> List[np.ndarray]:
        try:
            messages = self.redis_client.xread(
                {self.stream_key: self.last_id},
                count=count,
                block=1000
            )
            flows = []
            for _, message_list in messages:
                for msg_id, msg_data in message_list:
                    try:
                        features = json.loads(msg_data.get("features", "[]"))
                        if len(features) == 85:
                            flows.append(np.array(features, dtype=np.float32))
                        self.last_id = msg_id
                    except Exception as e:
                        logger.warning(f"Flow parse error: {e}")
            return flows
        except redis.RedisError as e:
            logger.error(f"Redis error: {e}")
            return []

    def run_baseline_learning(self):
        logger.info(f"🚀 Starting UNSUPERVISED baseline learning for {self.baseline_hours} hours")
        logger.info("   Learning YOUR network's normality - NO CIC datasets, NO labels")
        
        # FIX: Use timedelta with fractional hours
        self.baseline_end = datetime.now() + timedelta(hours=self.baseline_hours)
        
        while self.running and datetime.now() < self.baseline_end:
            new_flows = self.consume_flows(count=1000)
            if new_flows:
                self.baseline_flows.extend(new_flows)
                elapsed_h = (datetime.now() - (self.baseline_end - timedelta(hours=self.baseline_hours))).total_seconds() / 3600
                remaining_h = (self.baseline_end - datetime.now()).total_seconds() / 3600
                logger.info(
                    f"📊 Baseline: {len(self.baseline_flows)} flows | "
                    f"Elapsed: {elapsed_h:.2f}h | Remaining: {remaining_h:.2f}h"
                )
            time.sleep(5)  # Faster polling for testing
        
        if len(self.baseline_flows) < 10:
            logger.error(f"Insufficient flows: {len(self.baseline_flows)} (need >10 for test)")
            return False
        
        baseline_array = np.array(self.baseline_flows)
        logger.info(f"Training autoencoder on {baseline_array.shape[0]} flows...")
        
        self.learner = BaselineLearner(input_dim=85)
        self.learner.train(baseline_array, epochs=30)  # Fewer epochs for testing
        
        self.model_registry.export_onnx(
            self.learner.model,
            self.learner.scaler,
            self.learner.threshold
        )
        
        self.state = "MONITORING"
        logger.info("✅ UNSUPERVISED baseline COMPLETE")
        logger.info(f"   Threshold: {self.learner.threshold:.4f} | Model deployed to {self.model_registry.latest_dir}")
        return True

    def run_monitoring(self):
        logger.info("👁️  MONITORING phase active (concept drift checks hourly)")
        while self.running:
            time.sleep(30)  # Short sleep for testing
            logger.info("💤 Monitoring... (no drift checks in test mode)")

    def run(self):
        logger.info("🚀 AI Learning Engine STARTED")
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis failed: {e}")
            return False
        
        # Skip baseline if model exists
        if (self.model_registry.latest_dir.exists() and 
            (self.model_registry.latest_dir / "model.onnx").exists()):
            logger.info("✅ Pre-trained model found - skipping baseline")
            self.state = "MONITORING"
        else:
            logger.info(f"⏳ Starting UNSUPERVISED baseline ({self.baseline_hours}h)...")
            if not self.run_baseline_learning():
                return False
        
        if self.state == "MONITORING":
            self.run_monitoring()
        return True

if __name__ == "__main__":
    model_dir = os.getenv("MODEL_DIR", "/models")
    os.makedirs(model_dir, exist_ok=True)
    
    engine = AILearningEngine()
    success = engine.run()
    sys.exit(0 if success else 1)