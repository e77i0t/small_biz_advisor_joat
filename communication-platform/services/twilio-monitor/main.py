import os
import logging
from uuid import uuid4, UUID
from fastapi import Request, HTTPException, status
from fastapi.responses import JSONResponse
from communication_platform.shared.service_base import ServiceBase
from communication_platform.shared.event_publisher import EventPublisher
from communication_platform.shared.events import MessageReceivedEvent, EventType
from .handlers import process_incoming_message
from .models import IncomingMessageRequest, MessageResponse
from .database import MessageDB
from sqlalchemy.orm import Session
from starlette.middleware.base import BaseHTTPMiddleware
import uvicorn
from datetime import datetime

# Service instance
service = ServiceBase("twilio-monitor", version="1.0.0")
app = service.app
logger = logging.getLogger("twilio_monitor.main")

# RabbitMQ URL from env or default
def get_rabbitmq_url():
    return os.getenv("RABBITMQ_URL", "amqp://dev:dev123@localhost:5672/")

publisher = EventPublisher(get_rabbitmq_url())

# Error handling middleware
@app.middleware("http")
async def error_handling_middleware(request: Request, call_next):
    try:
        response = await call_next(request)
        return response
    except HTTPException as exc:
        logger.error(f"HTTPException: {exc.detail}")
        return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})
    except Exception as exc:
        logger.exception("Unhandled exception")
        return JSONResponse(status_code=500, content={"detail": "Internal Server Error"})

@app.post("/incoming", response_model=MessageResponse)
async def incoming_message(request: Request, body: IncomingMessageRequest):
    trace_id = getattr(request.state, "trace_id", str(uuid4()))
    if not isinstance(trace_id, UUID):
        try:
            trace_id = UUID(trace_id)
        except Exception:
            trace_id = uuid4()
    # Dependency injection for DB session (example, adjust as needed)
    from communication_platform.shared.database import SessionLocal
    db: Session = SessionLocal()
    try:
        result = await process_incoming_message(body, trace_id, db)
        if result.get("status") != "received":
            raise HTTPException(status_code=400, detail=result.get("reason", "Unknown error"))
        # Publish event
        event = MessageReceivedEvent(
            event_id=uuid4(),
            event_type=EventType.MESSAGE_RECEIVED,
            timestamp=datetime.utcnow(),
            trace_id=trace_id,
            source_service="twilio-monitor",
            payload={"message_id": result["message_id"]}
        )
        publisher.publish(event, routing_key="message.received.sms")
        return MessageResponse(
            message_id=result["message_id"],
            status=result["status"],
            timestamp=datetime.utcnow()
        )
    finally:
        db.close()

if __name__ == "__main__":
    uvicorn.run("communication_platform.services.twilio-monitor.main:app", host="0.0.0.0", port=8000, reload=True) 