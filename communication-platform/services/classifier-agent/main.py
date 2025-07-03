# Entry point for the Classifier Agent service

import os
from fastapi import Request, HTTPException
from uuid import uuid4, UUID
from communication_platform.shared.service_base import ServiceBase
from .models import ClassificationRequest, ClassificationResponse
from .handlers import classify_conversation
from .events import start_event_consumption
from communication_platform.shared.models import ConversationCategory
import openai

service = ServiceBase("classifier-agent", version="1.0.0")
app = service.app

@app.on_event("startup")
def on_startup():
    # Validate OPENAI_API_KEY
    if not os.getenv("OPENAI_API_KEY"):
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")
    # Start event consumption in a background thread
    import threading
    thread = threading.Thread(target=start_event_consumption, daemon=True)
    thread.start()

@app.post("/classify", response_model=ClassificationResponse)
async def classify_endpoint(request: ClassificationRequest, req: Request):
    trace_id = getattr(req.state, "trace_id", str(uuid4()))
    try:
        result = await classify_conversation(request.conversation_id, UUID(trace_id))
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Classification failed: {e}")

@app.get("/categories")
def get_categories():
    return {"categories": [cat.value for cat in ConversationCategory]}

@app.get("/health")
async def health_check():
    # Base health info
    health = {
        "status": "ok",
        "service": "classifier-agent",
        "timestamp": str(uuid4()),
        "openai_api_key_set": bool(os.getenv("OPENAI_API_KEY")),
        "openai_api_status": "unknown"
    }
    # Check OpenAI API connectivity
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            openai.api_key = api_key
            # Use a lightweight API call to check connectivity
            openai.Model.list()
            health["openai_api_status"] = "ok"
        except Exception as e:
            health["openai_api_status"] = f"error: {e}"
    else:
        health["openai_api_status"] = "not set"
    return health

if __name__ == "__main__":
    pass 