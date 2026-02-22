import redis
import os
from dotenv import load_dotenv

load_dotenv()

r = redis.Redis(
    host=os.getenv('REDIS_HOST', 'localhost'),
    port=int(os.getenv('REDIS_PORT', 6379)),
    password=os.getenv('REDIS_PASSWORD'),
    decode_responses=True
)

try:
    r.ping()
    print("✅ Redis connection successful")
    
    # Test stream
    msg_id = r.xadd("nids:flows:stream", {"test": "flow_data"})
    print(f"✅ Stream write successful (ID: {msg_id})")
    
    r.delete("nids:flows:stream")
    print("✅ Test cleanup complete")
except Exception as e:
    print(f"❌ Error: {e}")