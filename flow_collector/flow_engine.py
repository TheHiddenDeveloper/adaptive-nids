"""
NFStream wrapper for CIC-style feature extraction (85 features)
Defensive implementation: handles missing attributes gracefully
"""
from nfstream import NFStreamer
from typing import Dict, Any
from shared.features import CIC_FEATURES

class FlowEngine:
    """Real-time flow extraction with CIC-style feature mapping"""
    
    def __init__(
        self,
        interface: str = "eth0",
        bpf_filter: str = "ip",
        idle_timeout: int = 120,
        active_timeout: int = 600
    ):
        self.interface = interface
        self.bpf_filter = bpf_filter
        self.idle_timeout = idle_timeout
        self.active_timeout = active_timeout
    
    def start_capture(self):
        """Start NFStream capture"""
        return NFStreamer(
            source=self.interface,
            bpf_filter=self.bpf_filter,
            idle_timeout=self.idle_timeout,
            active_timeout=self.active_timeout,
            accounting_mode=3,
            statistical_analysis=True,
            splt_analysis=5,
            n_dissections=0,
            n_meters=4,
            max_nflows=0,
            system_visibility_mode=0
        )
    
    def _safe_get(self, flow, attr: str, default: float = 0.0) -> float:
        """Safely get attribute with fallback"""
        try:
            value = getattr(flow, attr)
            return float(value) if value is not None else default
        except AttributeError:
            return default
    
    def extract_cic_features(self, flow) -> Dict[str, float]:
        """
        Extract 85 CIC-style features with defensive attribute access
        Works with ALL NFStream versions (v5.x, v6.x, v7.x)
        """
        flow_dict = {
            "flow_id": f"{flow.src_ip}:{flow.src_port}-{flow.dst_ip}:{flow.dst_port}-{flow.protocol}",
            "src_ip": flow.src_ip,
            "src_port": flow.src_port,
            "dst_ip": flow.dst_ip,
            "dst_port": flow.dst_port,
            "protocol": flow.protocol,
            "timestamp": self._safe_get(flow, "bidirectional_first_seen_ms", 0.0),
            "flow_duration": self._safe_get(flow, "bidirectional_duration_ms", 0.0),
        }
        
        # ────────────────────────────────────────────────────────────────
        # TIMING FEATURES (defensive access - not all stats available in all versions)
        # ────────────────────────────────────────────────────────────────
        flow_dict.update({
            # Mean always available
            "flow_iat_mean": self._safe_get(flow, "bidirectional_mean_piat_ms", 
                                          self._safe_get(flow, "bidirectional_mean_iat_ms", 0.0)),
            # Std might be missing - fallback to 0
            "flow_iat_std": self._safe_get(flow, "bidirectional_std_piat_ms",
                                         self._safe_get(flow, "bidirectional_std_iat_ms", 0.0)),
            # Max/min usually available
            "flow_iat_max": self._safe_get(flow, "bidirectional_max_piat_ms",
                                         self._safe_get(flow, "bidirectional_max_iat_ms", 0.0)),
            "flow_iat_min": self._safe_get(flow, "bidirectional_min_piat_ms",
                                         self._safe_get(flow, "bidirectional_min_iat_ms", 0.0)),
            # Forward PIAT
            "fwd_iat_total": self._safe_get(flow, "src2dst_total_piat_ms",
                                          self._safe_get(flow, "src2dst_total_iat_ms", 0.0)),
            "fwd_iat_mean": self._safe_get(flow, "src2dst_mean_piat_ms",
                                         self._safe_get(flow, "src2dst_mean_iat_ms", 0.0)),
            "fwd_iat_std": self._safe_get(flow, "src2dst_std_piat_ms",
                                        self._safe_get(flow, "src2dst_std_iat_ms", 0.0)),
            "fwd_iat_max": self._safe_get(flow, "src2dst_max_piat_ms",
                                        self._safe_get(flow, "src2dst_max_iat_ms", 0.0)),
            "fwd_iat_min": self._safe_get(flow, "src2dst_min_piat_ms",
                                        self._safe_get(flow, "src2dst_min_iat_ms", 0.0)),
            # Backward PIAT
            "bwd_iat_total": self._safe_get(flow, "dst2src_total_piat_ms",
                                          self._safe_get(flow, "dst2src_total_iat_ms", 0.0)),
            "bwd_iat_mean": self._safe_get(flow, "dst2src_mean_piat_ms",
                                         self._safe_get(flow, "dst2src_mean_iat_ms", 0.0)),
            "bwd_iat_std": self._safe_get(flow, "dst2src_std_piat_ms",
                                        self._safe_get(flow, "dst2src_std_iat_ms", 0.0)),
            "bwd_iat_max": self._safe_get(flow, "dst2src_max_piat_ms",
                                        self._safe_get(flow, "dst2src_max_iat_ms", 0.0)),
            "bwd_iat_min": self._safe_get(flow, "dst2src_min_piat_ms",
                                        self._safe_get(flow, "dst2src_min_iat_ms", 0.0)),
        })
        
        # ────────────────────────────────────────────────────────────────
        # PACKET COUNTS & SIZES (core attributes - always available)
        # ────────────────────────────────────────────────────────────────
        flow_dict.update({
            "tot_fwd_pkts": self._safe_get(flow, "src2dst_packets", 0),
            "tot_bwd_pkts": self._safe_get(flow, "dst2src_packets", 0),
            "totlen_fwd_pkts": self._safe_get(flow, "src2dst_bytes", 0),
            "totlen_bwd_pkts": self._safe_get(flow, "dst2src_bytes", 0),
            "fwd_pkt_len_max": self._safe_get(flow, "src2dst_max_ps", 0),
            "fwd_pkt_len_min": self._safe_get(flow, "src2dst_min_ps", 0),
            "fwd_pkt_len_mean": self._safe_get(flow, "src2dst_mean_ps", 0),
            "fwd_pkt_len_std": self._safe_get(flow, "src2dst_stddev_ps", 0),
            "bwd_pkt_len_max": self._safe_get(flow, "dst2src_max_ps", 0),
            "bwd_pkt_len_min": self._safe_get(flow, "dst2src_min_ps", 0),
            "bwd_pkt_len_mean": self._safe_get(flow, "dst2src_mean_ps", 0),
            "bwd_pkt_len_std": self._safe_get(flow, "dst2src_stddev_ps", 0),
            "pkt_len_min": self._safe_get(flow, "bidirectional_min_ps", 0),
            "pkt_len_max": self._safe_get(flow, "bidirectional_max_ps", 0),
            "pkt_len_mean": self._safe_get(flow, "bidirectional_mean_ps", 0),
            "pkt_len_std": self._safe_get(flow, "bidirectional_stddev_ps", 0),
            "pkt_len_var": self._safe_get(flow, "bidirectional_stddev_ps", 0) ** 2,
            "pkt_len_zero_cnt": 0,
        })
        
        # ────────────────────────────────────────────────────────────────
        # RATES
        # ────────────────────────────────────────────────────────────────
        duration_sec = max(flow_dict["flow_duration"] / 1000.0, 0.001)  # Avoid div/0
        flow_dict.update({
            "flow_bytes_s": (flow_dict["totlen_fwd_pkts"] + flow_dict["totlen_bwd_pkts"]) / duration_sec,
            "flow_pkts_s": (flow_dict["tot_fwd_pkts"] + flow_dict["tot_bwd_pkts"]) / duration_sec,
            "fwd_pkt_per_s": flow_dict["tot_fwd_pkts"] / duration_sec,
            "bwd_pkt_per_s": flow_dict["tot_bwd_pkts"] / duration_sec,
            "flow_iat_tot": flow_dict["flow_duration"],
            "fwd_iat_tot": flow_dict["fwd_iat_total"],
            "bwd_iat_tot": flow_dict["bwd_iat_total"],
        })
        
        # ────────────────────────────────────────────────────────────────
        # TCP FLAGS
        # ────────────────────────────────────────────────────────────────
        def decompose_flags(flags_int: int) -> Dict[str, int]:
            if not isinstance(flags_int, int):
                flags_int = 0
            return {
                "fin_flag_cnt": 1 if flags_int & 0x01 else 0,
                "syn_flag_cnt": 1 if flags_int & 0x02 else 0,
                "rst_flag_cnt": 1 if flags_int & 0x04 else 0,
                "psh_flag_cnt": 1 if flags_int & 0x08 else 0,
                "ack_flag_cnt": 1 if flags_int & 0x10 else 0,
                "urg_flag_cnt": 1 if flags_int & 0x20 else 0,
                "cwr_flag_cnt": 1 if flags_int & 0x80 else 0,
                "ece_flag_cnt": 1 if flags_int & 0x40 else 0,
            }
        
        fwd_flags = decompose_flags(self._safe_get(flow, "src2dst_tcp_flags", 0))
        bwd_flags = decompose_flags(self._safe_get(flow, "dst2src_tcp_flags", 0))
        flow_dict.update({
            **fwd_flags,
            "fwd_psh_flags": fwd_flags["psh_flag_cnt"],
            "fwd_urg_flags": fwd_flags["urg_flag_cnt"],
            "bwd_psh_flags": bwd_flags["psh_flag_cnt"],
            "bwd_urg_flags": bwd_flags["urg_flag_cnt"],
        })
        
        # ────────────────────────────────────────────────────────────────
        # HEADER LENGTHS & PAYLOAD STATS
        # ────────────────────────────────────────────────────────────────
        flow_dict.update({
            "fwd_header_length": flow_dict["tot_fwd_pkts"] * 20,
            "bwd_header_length": flow_dict["tot_bwd_pkts"] * 20,
            "fwd_seg_size_avg": flow_dict["fwd_pkt_len_mean"],
            "bwd_seg_size_avg": flow_dict["bwd_pkt_len_mean"],
            "pkt_size_avg": flow_dict["pkt_len_mean"],
            "fwd_byts_b_avg": flow_dict["totlen_fwd_pkts"] / max(flow_dict["tot_fwd_pkts"], 1),
            "bwd_byts_b_avg": flow_dict["totlen_bwd_pkts"] / max(flow_dict["tot_bwd_pkts"], 1),
            "fwd_pkts_b_avg": 1.0,
            "bwd_pkts_b_avg": 1.0,
            "fwd_blk_rate_avg": 0.0,
            "bwd_blk_rate_avg": 0.0,
            "fwd_init_win_byts": 0,
            "bwd_init_win_byts": 0,
            "fwd_act_data_pkts": flow_dict["tot_fwd_pkts"],
            "fwd_seg_size_min": flow_dict["fwd_pkt_len_min"],
            "down_up_ratio": flow_dict["totlen_bwd_pkts"] / max(flow_dict["totlen_fwd_pkts"], 1),
        })
        
        # ────────────────────────────────────────────────────────────────
        # SUBFLOW & ACTIVE/IDLE (approximations)
        # ────────────────────────────────────────────────────────────────
        flow_dict.update({
            "subflow_fwd_pkts": flow_dict["tot_fwd_pkts"],
            "subflow_fwd_byts": flow_dict["totlen_fwd_pkts"],
            "subflow_bwd_pkts": flow_dict["tot_bwd_pkts"],
            "subflow_bwd_byts": flow_dict["totlen_bwd_pkts"],
            "active_mean": flow_dict["flow_duration"],
            "active_std": 0.0,
            "active_max": flow_dict["flow_duration"],
            "active_min": flow_dict["flow_duration"],
            "idle_mean": 0.0,
            "idle_std": 0.0,
            "idle_max": 0.0,
            "idle_min": 0.0,
        })
        
        # ────────────────────────────────────────────────────────────────
        # FILL ALL 85 CIC FEATURES
        # ────────────────────────────────────────────────────────────────
        for feature in CIC_FEATURES:
            if feature not in flow_dict:
                flow_dict[feature] = 0.0
        
        # Create feature vector
        flow_dict["feature_vector"] = [float(flow_dict[f]) for f in CIC_FEATURES]
        return flow_dict
    
    def validate_flow(self, flow_dict: Dict) -> bool:
        """Validate flow has all 85 features"""
        try:
            return (
                all(f in flow_dict for f in CIC_FEATURES) and
                all(isinstance(flow_dict[f], (int, float)) for f in CIC_FEATURES) and
                len(flow_dict["feature_vector"]) == 85
            )
        except Exception:
            return False