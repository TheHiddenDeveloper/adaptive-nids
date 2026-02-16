# 📜 Adaptive NIDS Project Charter

## 🎯 CORE OBJECTIVE
Build a **self-learning, adaptive NIDS** that learns the **unique normal traffic patterns** of a specific target network during a baseline period (7–14 days), then detects deviations from *that network's* normality — **NOT** from static CIC/IDS2017 datasets.

> "Your network's 'normal' ≠ CIC dataset's 'normal'"

## 🔑 NON-NEGOTIABLE CONSTRAINTS

### 🚫 STRICT PROHIBITIONS
1. **NO CIC DATASET TRAINING FOR PRODUCTION MODELS**  
   → CIC-IDS2017/2018 datasets are for research only. Production models must learn from the target network's traffic.
   
2. **NO SUPERVISED LEARNING DURING BASELINE PHASE**  
   → Baseline learning must be UNSUPERVISED (autoencoder, isolation forest). No labels assumed to exist.
   
3. **NO JAVA/CICFLOWMETER IN PRODUCTION**  
   → Pure Python backend required (NFStream for flow extraction).
   
4. **NO STATIC THRESHOLDS**  
   → Thresholds must be adaptive (e.g., 95th percentile of reconstruction errors from baseline traffic).

### ✅ APPROVED TECHNICAL APPROACH
| Component | Approved Technology | Why |
|-----------|---------------------|-----|
| Flow Extraction | NFStream (Python) | Pure Python, handles modern protocols, no Java |
| Baseline Learning | Denoising Autoencoder (PyTorch) | Unsupervised, learns complex normal patterns |
| Model Format | ONNX (opset 11) | Maximum compatibility across runtimes |
| Communication | Redis Streams | Resilient buffering, backpressure handling |
| Thresholding | Adaptive (95th percentile) | Learns from baseline traffic distribution |

## 📏 SUCCESS METRICS
| Metric | Target | Measurement |
|--------|--------|-------------|
| False Positive Rate | <2% on normal traffic | After baseline period, on 24h of normal traffic |
| Baseline Duration | 7-14 days | Time to first model deployment |
| Concept Drift Detection | <1 hour | Time from traffic change to retraining trigger |
| Model Reload Time | <5 seconds | Service 1 downtime during update |

## 🔄 LEARNING PHASES
### Phase 1: Baseline Learning (Days 1-7)
- **Input**: Raw flow features from target network (NO labels)
- **Technique**: Unsupervised autoencoder training
- **Output**: ONNX model + adaptive threshold (95th percentile reconstruction error)
- **Service 1**: Feature extraction only (no alerts)

### Phase 2: Monitoring (Ongoing)
- **Detection**: Real-time inference using deployed model
- **Drift Check**: Hourly comparison of reconstruction error distribution
- **Human Feedback**: Analysts label false positives via API
- **Threshold**: Fixed until drift detected

### Phase 3: Relearning (Triggered)
- **Trigger**: Concept drift detected (reconstruction error >30% above baseline threshold)
- **Technique**: Incremental retraining (20% old baseline + 80% new flows)
- **Deployment**: Atomic model update via symlink swap
- **Impact**: <5 second inference pause in Service 1

## 🧭 REDIRECTION PHRASE
When discussions drift from core constraints, use:

> "Remember the charter: We are building an adaptive NIDS that learns **THIS network's normality** — not a static detector trained on CIC datasets. No supervised learning during baseline. Pure Python backend. Two services with Redis streaming."

## 📜 DECISION LOG
| Date | Decision | Rationale |
|------|----------|-----------|
| 2026-02-08 | NFStream over CICFlowMeter | Pure Python requirement; better flow timeout handling |
| 2026-02-08 | Autoencoder for unsupervised learning | Learns complex normal patterns without labels |
| 2026-02-08 | ONNX opset 11 for export | Maximum compatibility across ONNX runtimes |
| 2026-02-08 | Redis Streams for communication | Resilient buffering, exactly-once processing |

## ✅ CHARTER COMPLIANCE CHECKLIST
Before any code change, verify:
- [ ] Does this require labeled data during baseline? → **REJECT**
- [ ] Does this use CIC datasets for production training? → **REJECT**
- [ ] Does this introduce Java dependencies? → **REJECT**
- [ ] Does this hardcode thresholds? → **REJECT**
- [ ] Does this break the two-service decoupled architecture? → **REJECT**

---
**This charter supersedes all other documentation.**  
When in doubt, refer to this document.  
*Last Updated: 2026-02-12*
```

---

### 💡 Deployment Instructions
```bash
# From project root (adaptive-nids/)
cat > README.md << 'EOF'
[PASTE ROOT README CONTENT ABOVE]
EOF

mkdir -p flow_collector ai_engine
cat > flow_collector/README.md << 'EOF'
[PASTE FLOW_COLLECTOR README CONTENT ABOVE]
EOF

cat > ai_engine/README.md << 'EOF'
[PASTE AI_ENGINE README CONTENT ABOVE]
EOF

cat > PROJECT_CHARTER.md << 'EOF'
[PASTE PROJECT_CHARTER CONTENT ABOVE]
EOF

# Verify structure
tree -L 2 -I 'venv|__pycache__|.git'
```