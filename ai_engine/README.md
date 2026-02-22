# 🤖 Service 2: AI Learning Engine

Unsupervised adaptive learning engine that learns your network's normal traffic patterns.

## 🎯 Responsibilities
- Consumes flows from Redis Streams (`nids:flows:stream`)
- Performs **UNSUPERVISED baseline learning** (7-14 days, NO labels required)
- Trains denoising autoencoder on normal traffic patterns
- Calculates adaptive threshold (95th percentile reconstruction error)
- Deploys ONNX models to `/models/latest` for Service 1 consumption
- Detects concept drift and triggers incremental retraining
- Provides human feedback API to refine false positives

## 📦 Dependencies
```txt
torch>=2.0.0
scikit-learn>=1.3.0
redis>=5.0.0
fastapi>=0.100.0
uvicorn>=0.23.0
onnx>=1.14.0
onnxscript>=0.1.0            # required by newer torch/onnx exports
joblib>=1.3.0
```

## ⚙️ Configuration
| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `BASELINE_HOURS` | `168` | Baseline duration (7 days = 168 hours) |
| `MODEL_DIR` | `/models` | Root directory for model artifacts |
| `ANALYST_ID` | `unknown` | Identifier for human feedback |

## 🚀 Usage
### Testing Baseline Learning (1 Minute)
```bash
python generate_test_flows.py  # Creates 200 synthetic flows
export BASELINE_HOURS=0.0167
python main.py
```

### Production Baseline Learning (7 Days)
```bash
export BASELINE_HOURS=168
python main.py
```

### Human Feedback API
```bash
# Start feedback endpoint (port 8001)
python feedback_api.py

# Submit feedback
curl -X POST http://localhost:8001/api/feedback \
  -H "Content-Type: application/json" \
  -d '{
    "flow_id": "192.168.1.100:45678-10.0.0.5:80-6",
    "is_true_positive": false,
    "analyst_notes": "Benign internal scan",
    "confidence": 0.95
  }'
```

## 📁 Model Deployment Structure
```
models/
├── latest/ → archive/v_20260212_143000
│   ├── model.onnx          # ONNX model (opset 11)
│   ├── scaler.pkl          # Feature scaler
│   └── metadata.json       # Threshold, feature count, etc.
└── archive/
    └── v_20260212_143000/
        ├── model.onnx
        ├── scaler.pkl
        └── metadata.json
```

## 📊 metadata.json Example
```json
{
  "version": "v_20260212_143000",
  "exported_at": "2026-02-12T14:30:00Z",
  "threshold": 0.1543,
  "feature_count": 85,
  "model_type": "denoising_autoencoder",
  "training_flows": "unsupervised_baseline",
  "adaptive_threshold_percentile": 95,
  "opset_version": 11
}
```

## 🔄 Learning Phases
| Phase | Duration | Action | Service 1 Behavior |
|-------|----------|--------|-------------------|
| **Baseline Learning** | 7-14 days | Unsupervised autoencoder training | Feature extraction only (no alerts) |
| **Monitoring** | Ongoing | Concept drift checks + human feedback | Real-time anomaly detection |
| **Relearning** | Triggered | Incremental model update | Brief inference pause (<5s) |

## 📌 Critical Design Principles
- **NO SUPERVISED LEARNING**: Baseline phase uses ZERO labels
- **NO CIC DATASETS**: Learns exclusively from your network's traffic
- **ADAPTIVE THRESHOLD**: Dynamically calculated from baseline traffic distribution
- **INCREMENTAL RETRAINING**: Combines old baseline (20%) + new flows (80%) to avoid catastrophic forgetting
- **COLD-START SAFE**: Service 1 operates without model during baseline phase

## 🧪 Testing Tools
```bash
# Generate synthetic flows (testing only)
python generate_test_flows.py

# Verify model deployment
ls -lh models/latest/
cat models/latest/metadata.json | python -m json.tool
```

## 🛠️ Troubleshooting
| Issue | Solution |
|-------|----------|
| "Insufficient flows" error | Generate test flows or wait for real traffic |
| ONNX export fails | Ensure opset_version=11 (configured in model_registry.py) |
| Symlink errors | Delete `models/latest` directory and restart |
| `ModuleNotFoundError: No module named 'onnxscript'` | install `onnxscript` (e.g. `pip install onnxscript`) or add to your environment |
| Concept drift false positives | Increase drift ratio threshold in `concept_drift.py` (default: 1.3x) |

---
*Part of Adaptive NIDS architecture | [Project Root](../README.md) | [Project Charter](../PROJECT_CHARTER.md)*