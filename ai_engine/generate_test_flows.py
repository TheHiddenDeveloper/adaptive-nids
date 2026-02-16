#!/usr/bin/env python3
"""
Generate synthetic normal traffic flows for baseline learning testing
Creates realistic flow patterns mimicking typical office network traffic
"""
import redis
import json
import time
import numpy as np
from datetime import datetime
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from shared.features import CIC_FEATURES

def generate_normal_flow(base_idx: int) -> dict:
    """Generate realistic 'normal' flow features (non-malicious patterns)"""
    # Simulate typical office traffic patterns
    flow_duration = np.random.gamma(2, 300)  # Most flows < 5min
    tot_fwd_pkts = max(1, int(np.random.lognormal(2, 1)))
    tot_bwd_pkts = max(1, int(np.random.lognormal(2, 1)))
    totlen_fwd_pkts = tot_fwd_pkts * np.random.randint(50, 1400)
    totlen_bwd_pkts = tot_bwd_pkts * np.random.randint(50, 1400)
    
    # Realistic timing patterns
    flow_iat_mean = max(1, flow_duration / (tot_fwd_pkts + tot_bwd_pkts + 1))
    flow_iat_std = flow_iat_mean * np.random.uniform(0.1, 0.5)
    
    # Build feature dictionary matching CIC schema
    flow = {
        "flow_id": f"synth_{base_idx}_{int(time.time()*1000)}",
        "src_ip": f"192.168.1.{np.random.randint(100,200)}",
        "src_port": np.random.randint(49152, 65535),
        "dst_ip": f"10.0.0.{np.random.randint(5,50)}",
        "dst_port": np.random.choice([80, 443, 53, 25, 143, 3389], p=[0.4,0.35,0.1,0.05,0.05,0.05]),
        "protocol": np.random.choice([6, 17], p=[0.85, 0.15]),  # TCP/UDP
        "timestamp": int(time.time() * 1000),
        "flow_duration": flow_duration,
        "flow_iat_mean": flow_iat_mean,
        "flow_iat_std": flow_iat_std,
        "flow_iat_max": flow_iat_mean * np.random.uniform(2, 5),
        "flow_iat_min": max(0.1, flow_iat_mean * np.random.uniform(0.1, 0.5)),
        "fwd_iat_total": flow_duration * 0.6,
        "fwd_iat_mean": flow_iat_mean * 0.9,
        "fwd_iat_std": flow_iat_std * 0.8,
        "fwd_iat_max": flow_iat_mean * 3,
        "fwd_iat_min": max(0.1, flow_iat_mean * 0.2),
        "bwd_iat_total": flow_duration * 0.4,
        "bwd_iat_mean": flow_iat_mean * 1.1,
        "bwd_iat_std": flow_iat_std * 1.2,
        "bwd_iat_max": flow_iat_mean * 4,
        "bwd_iat_min": max(0.1, flow_iat_mean * 0.3),
        "tot_fwd_pkts": tot_fwd_pkts,
        "tot_bwd_pkts": tot_bwd_pkts,
        "totlen_fwd_pkts": totlen_fwd_pkts,
        "totlen_bwd_pkts": totlen_bwd_pkts,
        "fwd_pkt_len_max": np.random.randint(500, 1500),
        "fwd_pkt_len_min": np.random.randint(40, 100),
        "fwd_pkt_len_mean": np.random.randint(200, 800),
        "fwd_pkt_len_std": np.random.randint(50, 300),
        "bwd_pkt_len_max": np.random.randint(500, 1500),
        "bwd_pkt_len_min": np.random.randint(40, 100),
        "bwd_pkt_len_mean": np.random.randint(200, 800),
        "bwd_pkt_len_std": np.random.randint(50, 300),
        "pkt_len_min": min(40, np.random.randint(40, 100)),
        "pkt_len_max": max(1000, np.random.randint(800, 1500)),
        "pkt_len_mean": np.random.randint(300, 900),
        "pkt_len_std": np.random.randint(100, 400),
        "pkt_len_var": np.random.randint(10000, 160000),
        "pkt_len_zero_cnt": 0,
        "flow_bytes_s": (totlen_fwd_pkts + totlen_bwd_pkts) / max(flow_duration/1000, 0.1),
        "flow_pkts_s": (tot_fwd_pkts + tot_bwd_pkts) / max(flow_duration/1000, 0.1),
        "fwd_pkt_per_s": tot_fwd_pkts / max(flow_duration/1000, 0.1),
        "bwd_pkt_per_s": tot_bwd_pkts / max(flow_duration/1000, 0.1),
        "flow_iat_tot": flow_duration,
        "fwd_iat_tot": flow_duration * 0.6,
        "bwd_iat_tot": flow_duration * 0.4,
        "fin_flag_cnt": 1 if np.random.random() < 0.7 else 0,
        "syn_flag_cnt": 1 if np.random.random() < 0.6 else 0,
        "rst_flag_cnt": 1 if np.random.random() < 0.1 else 0,
        "psh_flag_cnt": 1 if np.random.random() < 0.5 else 0,
        "ack_flag_cnt": 1,
        "urg_flag_cnt": 0,
        "cwr_flag_cnt": 0,
        "ece_flag_cnt": 0,
        "fwd_psh_flags": 1 if np.random.random() < 0.4 else 0,
        "bwd_psh_flags": 1 if np.random.random() < 0.3 else 0,
        "fwd_urg_flags": 0,
        "bwd_urg_flags": 0,
        "fwd_header_length": tot_fwd_pkts * 20,
        "bwd_header_length": tot_bwd_pkts * 20,
        "fwd_pkts_s": tot_fwd_pkts / max(flow_duration/1000, 0.1),
        "bwd_pkts_s": tot_bwd_pkts / max(flow_duration/1000, 0.1),
        "pkt_size_avg": (totlen_fwd_pkts + totlen_bwd_pkts) / max(tot_fwd_pkts + tot_bwd_pkts, 1),
        "fwd_seg_size_avg": totlen_fwd_pkts / max(tot_fwd_pkts, 1),
        "bwd_seg_size_avg": totlen_bwd_pkts / max(tot_bwd_pkts, 1),
        "fwd_byts_b_avg": totlen_fwd_pkts / max(tot_fwd_pkts, 1),
        "fwd_pkts_b_avg": 1.0,
        "fwd_blk_rate_avg": 0.0,
        "bwd_byts_b_avg": totlen_bwd_pkts / max(tot_bwd_pkts, 1),
        "bwd_pkts_b_avg": 1.0,
        "bwd_blk_rate_avg": 0.0,
        "subflow_fwd_pkts": tot_fwd_pkts,
        "subflow_fwd_byts": totlen_fwd_pkts,
        "subflow_bwd_pkts": tot_bwd_pkts,
        "subflow_bwd_byts": totlen_bwd_pkts,
        "fwd_init_win_byts": 0,
        "bwd_init_win_byts": 0,
        "fwd_act_data_pkts": tot_fwd_pkts,
        "fwd_seg_size_min": np.random.randint(40, 100),
        "active_mean": flow_duration,
        "active_std": 0.0,
        "active_max": flow_duration,
        "active_min": flow_duration,
        "idle_mean": 0.0,
        "idle_std": 0.0,
        "idle_max": 0.0,
        "idle_min": 0.0,
        "down_up_ratio": totlen_bwd_pkts / max(totlen_fwd_pkts, 1),
    }
    
    # Fill any missing CIC features with 0
    for feature in CIC_FEATURES:
        if feature not in flow:
            flow[feature] = 0.0
    
    # Create feature vector
    flow["feature_vector"] = [float(flow[f]) for f in CIC_FEATURES]
    return flow

def stream_flows(redis_client, count: int = 200, delay_ms: int = 10):
    """Stream synthetic flows to Redis"""
    print(f"🚀 Generating {count} synthetic normal flows...")
    for i in range(count):
        flow = generate_normal_flow(i)
        features = flow.pop("feature_vector")
        
        redis_client.xadd(
            "nids:flows:stream",
            {
                "flow_id": flow["flow_id"],
                "src_ip": flow["src_ip"],
                "dst_ip": flow["dst_ip"],
                "src_port": str(flow["src_port"]),
                "dst_port": str(flow["dst_port"]),
                "protocol": str(flow["protocol"]),
                "timestamp": str(flow["timestamp"]),
                "flow_duration": str(flow["flow_duration"]),
                "features": json.dumps([float(x) for x in features]),
                "collector_timestamp": str(time.time()),
                "collector_host": "synthetic_generator"
            },
            maxlen=100000,
            approximate=True
        )
        
        if (i + 1) % 50 == 0:
            print(f"  → Generated {i+1}/{count} flows")
        time.sleep(delay_ms / 1000.0)
    
    print(f"✅ {count} synthetic flows streamed to Redis")
    print(f"   Verify: redis-cli XLEN nids:flows:stream")

if __name__ == "__main__":
    # Connect to Redis
    r = redis.Redis(
        host=os.getenv("REDIS_HOST", "localhost"),
        port=int(os.getenv("REDIS_PORT", "6379")),
        password=os.getenv("REDIS_PASSWORD", None),
        decode_responses=True
    )
    
    try:
        r.ping()
        print("✅ Connected to Redis")
    except Exception as e:
        print(f"❌ Redis connection failed: {e}")
        sys.exit(1)
    
    # Generate 200 flows (enough for baseline learning test)
    stream_flows(r, count=200, delay_ms=5)