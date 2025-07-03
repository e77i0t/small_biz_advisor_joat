import asyncio
import logging
from uuid import uuid4, UUID
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from .models import GroupingRequest, GroupingResponse
from .handlers import group_messages
from .events import start_event_consumption, subscriber, setup_event_subscriber
from ...shared.service_base import ServiceBase
from datetime import datetime

service = ServiceBase("conversation-grouper", version="1.0.0")
app = service.app
logger = logging.getLogger("conversation_grouper.main")

# Track event consumer status
event_consumer_status = {"running": False}

def run_event_consumer_bg():
    event_consumer_status["running"] = True
    try:
        start_event_consumption()
    except Exception as e:
        logger.exception(f"Event consumer stopped: {e}")
        event_consumer_status["running"] = False

@app.on_event("startup")
async def startup_event():
    setup_event_subscriber()
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, run_event_consumer_bg)
    logger.info("Started event consumer in background.")

@app.post("/group", response_model=GroupingResponse)
async def group_endpoint(request: GroupingRequest, req: Request):
    trace_id = getattr(req.state, "trace_id", None)
    if not trace_id or not isinstance(trace_id, UUID):
        trace_id = uuid4()
    try:
        response = await group_messages(request.message_ids, trace_id)
        return response
    except Exception as e:
        logger.exception(f"Error in /group: {e}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@app.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": service.service_name,
        "timestamp": datetime.utcnow().isoformat(),
        "event_consumer_status": event_consumer_status["running"]
    } 