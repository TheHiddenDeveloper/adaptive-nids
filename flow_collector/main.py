#!/usr/bin/env python3
"""
Service 1: Production Flow Collector
- Captures traffic via NFStream
- Extracts 85 CIC-style features
- Streams to Redis
- Runs ONNX inference for real-time anomaly detection
- Cold-start safe: operates without model during baseline phase
"""
import os
import sys
import time
import json
import signal
from pathlib import Path
from typing import Dict
import redis
import numpy as np
import logging

# Project imports
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
sys.path.insert(0, str(PROJECT_ROOT))

from flow_collector.flow_engine import FlowEngine
from flow_collector.inference import ONNXInferenceEngine
from shared.features import CIC_FEATURES

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("FlowCollector")

class FlowCollectorService:
    def __init__(self):
        # Redis config
        self.redis_client = redis.Redis(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6380")),
            password=os.getenv("REDIS_PASSWORD", None),
            decode_responses=True,
            socket_connect_timeout=5
        )
        self.redis_stream = "nids:flows:stream"
        self.redis_maxlen = 100000
        
        # Capture config
        self.interface = os.getenv("CAPTURE_INTERFACE", "sample.pcap")
        self.bpf_filter = os.getenv("BPF_FILTER", "ip")
        
        # Model config
        self.model_dir = os.getenv("MODEL_DIR", str(PROJECT_ROOT / "models" / "latest"))
        self.inference_engine = None
        
        self.running = True
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)
    
    def shutdown(self, signum, frame):
        logger.info("🛑 Shutdown requested")
        self.running = False
    
    def resolve_source(self, source: str) -> str:
        """Resolve PCAP path to absolute path"""
        source_path = Path(source)
        
        # Interface names (no extension)
        if not source_path.suffix and (Path(f"/sys/class/net/{source}").exists() or source in ["any", "lo"]):
            return source
        
        # PCAP file - resolve to absolute path
        if not source_path.is_absolute():
            candidates = [
                PROJECT_ROOT / "flow_collector" / source,
                Path.cwd() / source
            ]
            for cand in candidates:
                if cand.exists():
                    return str(cand.absolute())
        
        return str(source_path.absolute()) if source_path.exists() else source
    
    def load_model(self):
        """Load ONNX model if available"""
        logger.info(f"🔍 Checking for model at {self.model_dir}...")
        self.inference_engine = ONNXInferenceEngine(self.model_dir)
        
        if self.inference_engine.is_loaded:
            logger.info("✅ Model loaded - real-time anomaly detection ACTIVE")
        else:
            logger.warning("⚠️ No model loaded - operating in feature extraction mode only (cold start)")
    
    def stream_flow(self, flow_dict: Dict) -> bool:
        """Stream flow to Redis"""
        try:
            feature_vec = flow_dict.pop("feature_vector", [])
            flow_dict["features"] = json.dumps([float(x) for x in feature_vec])
            flow_dict["timestamp"] = time.time()
            
            self.redis_client.xadd(
                self.redis_stream,
                {k: str(v) for k, v in flow_dict.items()},
                maxlen=self.redis_maxlen,
                approximate=True
            )
            flow_dict["feature_vector"] = feature_vec
            return True
        except Exception as e:
            logger.warning(f"⚠️ Redis error: {e}")
            return False
    
    def detect_anomaly(self, flow_dict: Dict) -> Dict:
        """Run inference and return detection result"""
        if not self.inference_engine or not self.inference_engine.is_loaded:
            return {"is_anomaly": False, "anomaly_score": 0.0, "mode": "cold_start"}
        
        try:
            features = np.array([flow_dict["feature_vector"]], dtype=np.float32)
            anomaly_score, reconstruction_error = self.inference_engine.predict(features)
            
            is_anomaly = anomaly_score > 1.0  # Score > 1.0 = above threshold
            
            return {
                "is_anomaly": is_anomaly,
                "anomaly_score": float(anomaly_score),
                "reconstruction_error": float(reconstruction_error),
                "threshold": self.inference_engine.threshold,
                "mode": "inference"
            }
        except Exception as e:
            logger.warning(f"⚠️ Detection error: {e}")
            return {"is_anomaly": False, "anomaly_score": 0.0, "mode": "error"}
    
    def run(self):
        logger.info("🚀 Starting Flow Collector Service")
        logger.info(f"   Source: {self.interface}")
        logger.info(f"   Redis: {os.getenv('REDIS_HOST', 'localhost')}:{os.getenv('REDIS_PORT', '6380')}")
        logger.info(f"   Model dir: {self.model_dir}")
        
        # Test Redis
        try:
            self.redis_client.ping()
            logger.info("✅ Redis connected")
        except Exception as e:
            logger.error(f"❌ Redis connection failed: {e}")
            return False
        
        # Load model (if available)
        self.load_model()
        
        # Resolve capture source
        resolved_source = self.resolve_source(self.interface)
        logger.info(f"   Resolved source: {resolved_source}")
        
        # Initialize flow engine
        engine = FlowEngine(
            interface=resolved_source,
            bpf_filter=self.bpf_filter
        )
        
        try:
            streamer = engine.start_capture()
            flow_count = 0
            anomaly_count = 0
            
            for flow in streamer:
                if not self.running:
                    break
                
                # Extract features
                flow_dict = engine.extract_cic_features(flow)
                if not engine.validate_flow(flow_dict):
                    continue
                
                # Stream to AI engine
                self.stream_flow(flow_dict)
                
                # Real-time detection
                detection = self.detect_anomaly(flow_dict)
                
                # Log flow with detection result
                src = f"{flow_dict['src_ip']}:{flow_dict['src_port']}"
                dst = f"{flow_dict['dst_ip']}:{flow_dict['dst_port']}"
                pkts = flow_dict['tot_fwd_pkts'] + flow_dict['tot_bwd_pkts']
                
                if detection["is_anomaly"]:
                    anomaly_count += 1
                    logger.warning(
                        f"🚨 ANOMALY [{detection['anomaly_score']:.2f}x] "
                        f"{src} → {dst} ({pkts:.0f} pkts, {flow_dict['flow_duration']:.0f}ms)"
                    )
                else:
                    logger.info(
                        f"✅ Flow {flow_count+1}: {src} → {dst} "
                        f"({pkts:.0f} pkts, score: {detection['anomaly_score']:.2f})"
                    )
                
                flow_count += 1
                if flow_count >= 5:  # Stop after 5 flows for test
                    break
            
            logger.info(f"⏹️  Test complete: {flow_count} flows processed, {anomaly_count} anomalies detected")
            logger.info(f"   Model status: {'ACTIVE' if self.inference_engine and self.inference_engine.is_loaded else 'COLD START'}")
            return True
            
        except Exception as e:
            logger.exception(f"❌ Capture error: {e}")
            return False

if __name__ == "__main__":
    # Default to sample.pcap if not set
    if "CAPTURE_INTERFACE" not in os.environ:
        os.environ["CAPTURE_INTERFACE"] = "sample.pcap"
    
    # Default model dir
    if "MODEL_DIR" not in os.environ:
        os.environ["MODEL_DIR"] = str(PROJECT_ROOT / "models" / "latest")
    
    service = FlowCollectorService()
    success = service.run()
    sys.exit(0 if success else 1)