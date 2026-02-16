
# 📡 Service 1: Flow Collector

Real-time network flow extraction and anomaly detection engine.

## 🎯 Responsibilities
- Captures live traffic via NFStream (or PCAP files for testing)
- Extracts **85 CIC-style flow features** per flow
- Streams flows to Redis (`nids:flows:stream`) for Service 2 consumption
- Runs **ONNX inference** using latest deployed model from Service 2
- Generates alerts for anomalous flows with confidence scores
- **Cold-start safe**: Operates in feature extraction mode during baseline phase

## 📦 Dependencies
```txt
nfstream>=6.3.0
redis>=5.0.0
onnxruntime>=1.16.0
numpy>=1.24.0
prometheus-client>=0.19.0
pydantic>=2.0.0
```

## ⚙️ Configuration
| Environment Variable | Default | Description |
|----------------------|---------|-------------|
| `CAPTURE_INTERFACE` | `sample.pcap` | Network interface (`eth0`) or PCAP path |
| `BPF_FILTER` | `ip` | Berkeley Packet Filter (e.g., `tcp port 80`) |
| `REDIS_HOST` | `localhost` | Redis server hostname |
| `REDIS_PORT` | `6379` | Redis server port |
| `MODEL_DIR` | `/models/latest` | Path to ONNX model directory |
| `METRICS_PORT` | `9090` | Prometheus metrics endpoint |

## 🚀 Usage
### Testing with PCAP (No Root)
```bash
unset CAPTURE_INTERFACE
export MODEL_DIR=$(pwd)/../models/latest
python main.py
```

### Production: Live Capture
```bash
# One-time capability setup
sudo setcap cap_net_raw,cap_net_admin+eip $(which python3)

# Run with live interface
export CAPTURE_INTERFACE=eth0
export MODEL_DIR=/models/latest
python main.py
```

### Docker Deployment
```bash
docker build -t nids-collector -f Dockerfile .
docker run -d \
  --network=host \
  --cap-add=NET_RAW \
  --cap-add=NET_ADMIN \
  -v $(pwd)/models:/models:ro \
  -e CAPTURE_INTERFACE=eth0 \
  nids-collector
```

## 📊 Metrics Endpoint
Access at `http://localhost:9090/metrics`:
```
nids_flows_total 1250
nids_anomalies_total 3
nids_model_loaded 1
nids_service_uptime_seconds 3600
```

## 🔍 Logging Output
```
2026-02-12 04:15:22 ✅ Flow 1: 192.168.1.100:45678 → 10.0.0.5:80 (4 pkts, score: 0.87)
2026-02-12 04:15:23 🚨 ANOMALY [2.31x] 192.168.1.100:45678 → 10.0.0.5:80 (1 pkts, 89ms)
```

## 🧪 Testing
```bash
# Test flow extraction
python test_engine.py

# Verify Redis connectivity
python ../test_redis.py
```

## 📌 Critical Notes
- **Manjaro/Arch**: `sudo pacman -S libpcap` for headers
- **Path Resolution**: Auto-resolves relative PCAP paths to absolute
- **NFStream v6+**: Uses `*_piat_*` attributes (Packet Inter-Arrival Time)
- **Cold Start**: Operates without model during Service 2 baseline phase (logs warning but continues)
- **Feature Validation**: Skips flows with invalid feature counts (logs warning)

---
*Part of Adaptive NIDS architecture | [Project Root](../README.md) | [Project Charter](../PROJECT_CHARTER.md)*