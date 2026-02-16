#!/usr/bin/env python3
"""
Redis connectivity test - works from HOST machine
"""
import redis
import sys

def test_redis():
    r = redis.Redis(
        host='localhost',
        port=6379,
        password=None,
        db=0,
        socket_connect_timeout=5,
        decode_responses=True
    )
    
    try:
        r.ping()
        print("✅ Redis connection successful (localhost:6379)")
        
        stream_key = "nids:flows:stream"
        msg_id = r.xadd(stream_key, {
            "flow_id": "test_flow_123",
            "src_ip": "192.168.1.100",
            "dst_ip": "10.0.0.5",
            "timestamp": "2026-02-08T12:00:00Z",
            "flow_duration": "1250"
        })
        print(f"✅ Stream write successful (ID: {msg_id})")
        
        messages = r.xread({stream_key: "0-0"}, count=1)
        if messages:
            print(f"✅ Stream read successful ({len(messages[0][1])} message(s))")
        
        r.delete(stream_key)
        print("✅ Test cleanup complete")
        
        # Robust stats display (handles Redis version differences)
        info = r.info()
        mem = info.get('used_memory_human', 'N/A')
        uptime = info.get('uptime_in_seconds', info.get('rdb_last_save_time', 'N/A'))
        print(f"\n📊 Redis Stats: Memory={mem} | Uptime={uptime}s")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Testing Redis setup for Adaptive NIDS...\n")
    sys.exit(0 if test_redis() else 1)