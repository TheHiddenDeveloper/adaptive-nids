"""
Human feedback API - allows analysts to label alerts as FP/TP
Refines model during incremental retraining cycles
"""
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Optional
import redis
import json
import os

app = FastAPI(title="NIDS Human Feedback API", version="1.0.0")

# Redis connection
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=int(os.getenv("REDIS_PORT", "6379")),
    password=os.getenv("REDIS_PASSWORD", None),
    decode_responses=True
)

class FeedbackRequest(BaseModel):
    flow_id: str
    is_true_positive: bool  # True = real attack, False = false positive
    analyst_notes: Optional[str] = None
    confidence: float = 1.0  # Analyst confidence in labeling (0.0-1.0)

@app.post("/api/feedback")
async def submit_feedback(feedback: FeedbackRequest):
    """Submit human feedback for a flow/alert"""
    if not 0.0 <= feedback.confidence <= 1.0:
        raise HTTPException(status_code=400, detail="Confidence must be between 0.0 and 1.0")
    
    feedback_data = {
        "flow_id": feedback.flow_id,
        "is_true_positive": str(feedback.is_true_positive),
        "analyst_notes": feedback.analyst_notes or "",
        "confidence": str(feedback.confidence),
        "timestamp": str(time.time()),
        "analyst": os.getenv("ANALYST_ID", "unknown")
    }
    
    # Stream to Redis for consumption by learning engine
    redis_client.xadd(
        "nids:feedback:stream",
        {k: str(v) for k, v in feedback_data.items()},
        maxlen=100000
    )
    
    return {
        "status": "recorded",
        "message": "Feedback will be used in next model retraining cycle",
        "flow_id": feedback.flow_id
    }

@app.get("/api/feedback/stats")
async def feedback_stats():
    """Get feedback statistics"""
    total = redis_client.xlen("nids:feedback:stream")
    return {"total_feedback_items": total}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)