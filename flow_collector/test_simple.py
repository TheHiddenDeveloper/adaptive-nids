#!/usr/bin/env python3
"""
Ultra-simple NFStream test - works even with minimal PCAP
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from nfstream import NFStreamer
    print("✅ NFStream import successful")
except Exception as e:
    print(f"❌ NFStream import failed: {e}")
    print("   Fix: source ../venv/bin/activate && pip install nfstream")
    sys.exit(1)

# Use sample.pcap in current directory
pcap = "sample.pcap"
if not os.path.exists(pcap):
    print(f"❌ {pcap} not found - run PCAP generator first")
    sys.exit(1)

print(f"🔍 Reading {pcap}...")
try:
    streamer = NFStreamer(source=pcap, idle_timeout=1000)
    flows = list(streamer)
    print(f"✅ Successfully processed {len(flows)} flows")
    if flows:
        f = flows[0]
        print(f"   Flow 0: {f.src_ip}:{f.src_port} -> {f.dst_ip}:{f.dst_port}")
        print(f"   Duration: {f.bidirectional_duration_ms}ms")
        print(f"   Packets: {f.bidirectional_packets}")
    sys.exit(0)
except Exception as e:
    print(f"❌ NFStream error: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)