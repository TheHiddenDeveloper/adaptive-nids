"""
ONNX inference engine for real-time anomaly detection
Cold-start safe: operates without model during baseline phase
"""
import os
import json
import numpy as np
from pathlib import Path
import logging

logger = logging.getLogger("InferenceEngine")

class ONNXInferenceEngine:
    def __init__(self, model_dir: str = "/models/latest"):
        self.model_dir = Path(model_dir)
        self.session = None
        self.scaler = None
        self.threshold = 0.5
        self.feature_count = 85
        self._ort = None
        
        self._load_model()
    
    def _load_model(self):
        """Load ONNX model + scaler + threshold (cold-start safe)"""
        try:
            # Check if model exists
            onnx_path = self.model_dir / "model.onnx"
            if not onnx_path.exists():
                logger.warning(f"⚠️ No ONNX model found at {onnx_path} (cold start mode)")
                return
            
            # Load ONNX Runtime
            import onnxruntime as ort
            self._ort = ort
            self.session = ort.InferenceSession(str(onnx_path))
            logger.info(f"✅ Loaded ONNX model from {onnx_path}")
            
            # Load scaler
            import joblib
            scaler_path = self.model_dir / "scaler.pkl"
            if scaler_path.exists():
                self.scaler = joblib.load(scaler_path)
                logger.info(f"✅ Loaded feature scaler from {scaler_path}")
            else:
                logger.warning(f"⚠️ Scaler not found at {scaler_path} - using identity scaling")
                self.scaler = None
            
            # Load threshold from metadata
            metadata_path = self.model_dir / "metadata.json"
            if metadata_path.exists():
                with open(metadata_path) as f:
                    metadata = json.load(f)
                    self.threshold = metadata.get("threshold", 0.5)
                    self.feature_count = metadata.get("feature_count", 85)
                logger.info(f"✅ Loaded adaptive threshold: {self.threshold:.4f} (95th percentile)")
            else:
                logger.warning(f"⚠️ Metadata not found - using default threshold 0.5")
            
        except ImportError as e:
            logger.error(f"❌ onnxruntime not installed: {e}")
            logger.info("   Fix: pip install onnxruntime")
        except Exception as e:
            logger.error(f"❌ Model load failed: {type(e).__name__}: {e}")
    
    def predict(self, features: np.ndarray) -> tuple:
        """
        Returns (anomaly_score, reconstruction_error)
        anomaly_score = reconstruction_error / threshold (normalized)
        """
        if self.session is None:
            return 0.0, 0.0  # No model = no detection (cold start)
        
        try:
            # Scale features
            if self.scaler is not None:
                features_scaled = self.scaler.transform(features)
            else:
                features_scaled = features
            
            # Run inference
            input_name = self.session.get_inputs()[0].name
            outputs = self.session.run(None, {input_name: features_scaled.astype(np.float32)})
            reconstruction = outputs[0]
            
            # Calculate reconstruction error (MSE)
            reconstruction_error = np.mean((features_scaled - reconstruction) ** 2)
            
            # Normalize by threshold for consistent scoring
            anomaly_score = reconstruction_error / self.threshold
            
            return anomaly_score, reconstruction_error
            
        except Exception as e:
            logger.warning(f"⚠️ Inference error: {type(e).__name__}: {e}")
            return 0.0, 0.0
    
    @property
    def is_loaded(self) -> bool:
        return self.session is not None