
---

### 📄 `adaptive-nids/README.md`
```markdown
# 🌐 Adaptive Network Intrusion Detection System (NIDS)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-Apache_2.0-green.svg)](LICENSE)
[![Status](https://img.shields.io/badge/Status-Production_Ready-brightgreen.svg)](STATUS)

A **self-learning, adaptive NIDS** that learns your network's unique normal traffic patterns during a baseline period (7-14 days), then detects deviations from *your network's* normality — **NOT** from static CIC/IDS2017 datasets.

> 🔑 **Core Philosophy**: Your network's "normal" ≠ CIC dataset's "normal". This system learns *your* traffic patterns without labels or external datasets.

## ✨ Key Features
- **Pure Python Backend**: No Java/CICFlowMeter dependencies
- **Unsupervised Baseline Learning**: Learns normality from 7-14 days of traffic (NO labels required)
- **Adaptive Thresholding**: 95th percentile reconstruction error from baseline traffic
- **Concept Drift Handling**: Incremental retraining when traffic patterns change
- **Human-in-the-Loop**: Feedback API to refine false positives
- **Production-Ready**: Redis Streams for resilience, ONNX for fast inference, Prometheus metrics
- **<2% False Positives**: Target metric on normal traffic after baseline period

## 🏗️ Architecture
```
┌─────────────────────────────────────────────────────────────────────┐
│                    NETWORK (SPAN Port / TAP)                        │
└──────────────────────────────┬──────────────────────────────────────┘
                               │
┌──────────────────────────────▼──────────────────────────────────────┐
│  SERVICE 1: Flow Collector (flow_collector/)                        │
│  • Captures live traffic via NFStream                               │
│  • Extracts 85 CIC-style flow features                              │
│  • Streams to Redis (nids:flows:stream)                             │
│  • Runs ONNX inference using latest deployed model                  │
│  • Cold-start safe: operates without model during baseline phase    │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ (Redis Streams)
┌──────────────────────────────▼──────────────────────────────────────┐
│  SERVICE 2: AI Learning Engine (ai_engine/)                         │
│  • Consumes flows from Redis                                        │
│  • UNSUPERVISED baseline learning (7-14 days, NO labels)            │
│  • Deploys autoencoder models to /models/latest                     │
│  • Handles concept drift via incremental retraining                 │
│  • Human feedback API for false positive refinement                 │
└──────────────────────────────┬──────────────────────────────────────┘
                               │ (ONNX Model)
┌──────────────────────────────▼──────────────────────────────────────┐
│  SERVICE 1: Real-time Detection (with updated model)                │
│  • Detects deviations from learned baseline                         │
│  • Alerts on anomalies with confidence scores                       │
└─────────────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start (Manjaro/Arch Linux)
### Prerequisites
```bash
sudo pacman -Syu --needed libpcap base-devel python-pip redis
ldconfig -p | grep libpcap  # Verify installation
```

### Installation
```bash
git clone https://github.com/yourusername/adaptive-nids.git
cd adaptive-nids
python -m venv venv && source venv/bin/activate
pip install -r flow_collector/requirements.txt
pip install -r ai_engine/requirements.txt
docker-compose up -d redis
```

### Testing Workflow (5 Minutes)
```bash
# Terminal 1: Generate synthetic baseline flows
cd ai_engine && python generate_test_flows.py

# Terminal 1: Run baseline learning (60 seconds)
export BASELINE_HOURS=0.0167 && python main.py

# Terminal 2: Run flow collector with model loading
cd flow_collector
export MODEL_DIR=$(pwd)/../models/latest
python main.py
```

## 📁 Project Structure
```
adaptive-nids/
├── docker-compose.yml          # Redis + optional RedisInsight
├── .env.example                # Environment variables template
├── README.md                   # This file
├── PROJECT_CHARTER.md          # Non-negotiable constraints
│
├── flow_collector/             # SERVICE 1: Real-time flow capture + inference
│   ├── main.py
│   ├── flow_engine.py
│   ├── inference.py
│   ├── requirements.txt
│   └── README.md
│
├── ai_engine/                  # SERVICE 2: Unsupervised learning engine
│   ├── main.py
│   ├── baseline_learner.py
│   ├── model_registry.py
│   ├── concept_drift.py
│   ├── feedback_api.py
│   ├── generate_test_flows.py
│   ├── requirements.txt
│   └── README.md
│
├── shared/                     # Shared components
│   ├── features.py             # CIC-style feature schema (85 features)
│   └── config.py
│
├── models/                     # VOLUME: Model artifacts
│   ├── latest/ → v_20260212_...
│   └── archive/
│
└── data/                       # VOLUME: Flow storage (optional)
```

## ⚙️ Configuration
Copy `.env.example` to `.env`:
```env
# Redis
REDIS_HOST=localhost
REDIS_PORT=6379

# Network Capture
CAPTURE_INTERFACE=eth0          # Or sample.pcap for testing
BPF_FILTER=ip

# Baseline Learning
BASELINE_HOURS=168              # 7 days (production) | 0.0167 (1 min test)

# Model Deployment
MODEL_DIR=/models/latest
```

## 🧪 Testing
```bash
# Verify Redis
python test_redis.py

# Test flow extraction
cd flow_collector && python test_engine.py

# End-to-end test
cd ai_engine && python generate_test_flows.py && export BASELINE_HOURS=0.0167 && python main.py
cd flow_collector && export MODEL_DIR=$(pwd)/../models/latest && python main.py
```

## 🐳 Docker Deployment
```bash
docker-compose up -d
docker-compose logs -f flow-collector
docker-compose logs -f ai-engine
```

## 📊 Monitoring
- **Prometheus Metrics**: `http://localhost:9090/metrics`
- **RedisInsight GUI**: `http://localhost:8001`

## 🛠️ Troubleshooting
| Issue | Solution |
|-------|----------|
| `Permission denied` on capture | `sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)` |
| `No model loaded` warning | Complete baseline learning in Service 2 first |
| Redis connection failed | `docker-compose ps` → verify `nids-redis` running |
| NFStream import error | `CFLAGS="-I/usr/include/pcap" pip install --force-reinstall nfstream` |

## 📜 License
Apache License 2.0

## 🤝 Contributing
This project strictly follows the constraints defined in [`PROJECT_CHARTER.md`](PROJECT_CHARTER.md):
- ✅ UNSUPERVISED learning during baseline (NO labels)
- ✅ NO CIC dataset training for production models
- ✅ Pure Python backend (NO Java/CICFlowMeter)
- ✅ Learns THIS network's normality (not lab-generated traffic)

---
**Built with ❤️ for adaptive network security** | [Project Charter](PROJECT_CHARTER.md)
```