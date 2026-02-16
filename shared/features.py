"""
CIC-IDS2017 feature schema (85 features)
Used by BOTH services for consistent feature extraction/scoring
"""
from typing import List, Dict

# ────────────────────────────────────────────────────────────────────────
# CORE FEATURE SET (85 features matching CIC-IDS2017)
# ────────────────────────────────────────────────────────────────────────
CIC_FEATURES: List[str] = [
    # Flow basic info (7)
    "flow_duration", "flow_iat_mean", "flow_iat_std", "flow_iat_max", "flow_iat_min",
    "fwd_iat_total", "fwd_iat_mean",
    
    # Packet counts & sizes (12)
    "fwd_iat_std", "fwd_iat_max", "fwd_iat_min", "bwd_iat_total", "bwd_iat_mean",
    "bwd_iat_std", "bwd_iat_max", "bwd_iat_min", "fwd_psh_flags", "bwd_psh_flags",
    "fwd_urg_flags", "bwd_urg_flags",
    
    # Payload statistics (14)
    "fwd_header_length", "bwd_header_length", "fwd_packets_s", "bwd_packets_s",
    "pkt_len_min", "pkt_len_max", "pkt_len_mean", "pkt_len_std", "pkt_len_var",
    "fin_flag_cnt", "syn_flag_cnt", "rst_flag_cnt", "psh_flag_cnt", "ack_flag_cnt",
    
    # TCP flags & control (11)
    "urg_flag_cnt", "cwr_flag_cnt", "ece_flag_cnt", "down_up_ratio",
    "pkt_size_avg", "fwd_seg_size_avg", "bwd_seg_size_avg", "fwd_byts_b_avg",
    "fwd_pkts_b_avg", "fwd_blk_rate_avg", "bwd_byts_b_avg",
    
    # Subflow analysis (8)
    "bwd_pkts_b_avg", "bwd_blk_rate_avg", "subflow_fwd_pkts", "subflow_fwd_byts",
    "subflow_bwd_pkts", "subflow_bwd_byts", "fwd_init_win_byts", "bwd_init_win_byts",
    
    # Active/Idle times (8)
    "fwd_act_data_pkts", "fwd_seg_size_min", "active_mean", "active_std",
    "active_max", "active_min", "idle_mean", "idle_std",
    
    # Bidirectional flow stats (15)
    "idle_max", "idle_min", "tot_fwd_pkts", "tot_bwd_pkts", "totlen_fwd_pkts",
    "totlen_bwd_pkts", "fwd_pkt_len_max", "fwd_pkt_len_min", "fwd_pkt_len_mean",
    "fwd_pkt_len_std", "bwd_pkt_len_max", "bwd_pkt_len_min", "bwd_pkt_len_mean",
    "bwd_pkt_len_std", "pkt_len_zero_cnt",
    
    # Flow-level rates (10)
    "fwd_pkt_per_s", "bwd_pkt_per_s", "flow_bytes_s", "flow_pkts_s",
    "flow_iat_tot", "fwd_iat_tot", "bwd_iat_tot", "fwd_header_len_tot",
    "bwd_header_len_tot", "fwd_pkts_payload_tot"
]

# ────────────────────────────────────────────────────────────────────────
# NFSTREAM → CIC FEATURE MAPPING
# Maps NFStream's native features to CIC-IDS2017 schema
# ────────────────────────────────────────────────────────────────────────
NFSTREAM_TO_CIC_MAPPING: Dict[str, str] = {
    # Duration & timing
    "bidirectional_duration_ms": "flow_duration",
    "bidirectional_mean_iat_ms": "flow_iat_mean",
    "bidirectional_std_iat_ms": "flow_iat_std",
    "bidirectional_max_iat_ms": "flow_iat_max",
    "bidirectional_min_iat_ms": "flow_iat_min",
    
    # Forward direction
    "src2dst_total_iat_ms": "fwd_iat_total",
    "src2dst_mean_iat_ms": "fwd_iat_mean",
    "src2dst_std_iat_ms": "fwd_iat_std",
    "src2dst_max_iat_ms": "fwd_iat_max",
    "src2dst_min_iat_ms": "fwd_iat_min",
    "src2dst_packets": "tot_fwd_pkts",
    "src2dst_bytes": "totlen_fwd_pkts",
    
    # Backward direction
    "dst2src_total_iat_ms": "bwd_iat_total",
    "dst2src_mean_iat_ms": "bwd_iat_mean",
    "dst2src_std_iat_ms": "bwd_iat_std",
    "dst2src_max_iat_ms": "bwd_iat_max",
    "dst2src_min_iat_ms": "bwd_iat_min",
    "dst2src_packets": "tot_bwd_pkts",
    "dst2src_bytes": "totlen_bwd_pkts",
    
    # Packet sizes
    "bidirectional_min_ps": "pkt_len_min",
    "bidirectional_max_ps": "pkt_len_max",
    "bidirectional_mean_ps": "pkt_len_mean",
    "bidirectional_stddev_ps": "pkt_len_std",
    
    # TCP flags (NFStream provides these as flow-level aggregates)
    "src2dst_tcp_flags": "fwd_tcp_flags",  # Will be decomposed in feature_engine.py
    "dst2src_tcp_flags": "bwd_tcp_flags",
    
    # Rates
    "bidirectional_bytes_per_sec": "flow_bytes_s",
    "bidirectional_packets_per_sec": "flow_pkts_s",
}

# ────────────────────────────────────────────────────────────────────────
# FEATURE CATEGORIES (for analysis/debugging)
# ────────────────────────────────────────────────────────────────────────
FEATURE_CATEGORIES = {
    "timing": ["flow_duration", "flow_iat_mean", "flow_iat_std", "flow_iat_max", "flow_iat_min"],
    "packet_counts": ["tot_fwd_pkts", "tot_bwd_pkts", "pkt_len_zero_cnt"],
    "payload_sizes": ["totlen_fwd_pkts", "totlen_bwd_pkts", "pkt_len_min", "pkt_len_max", "pkt_len_mean"],
    "tcp_flags": ["fin_flag_cnt", "syn_flag_cnt", "rst_flag_cnt", "psh_flag_cnt", "ack_flag_cnt"],
    "rates": ["flow_bytes_s", "flow_pkts_s", "fwd_pkt_per_s", "bwd_pkt_per_s"],
    "active_idle": ["active_mean", "active_std", "idle_mean", "idle_std"]
}

def get_feature_count() -> int:
    """Return total number of features (should be 85)"""
    return len(CIC_FEATURES)

def validate_feature_vector(vec: list) -> bool:
    """Validate feature vector has correct length"""
    return len(vec) == get_feature_count()

if __name__ == "__main__":
    print(f"✅ CIC feature schema loaded: {get_feature_count()} features")
    print(f"   First 5 features: {CIC_FEATURES[:5]}")
    print(f"   NFStream mappings: {len(NFSTREAM_TO_CIC_MAPPING)} native features mapped")
