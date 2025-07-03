import re
import logging
from uuid import UUID
from datetime import datetime
from sqlalchemy.orm import Session
from communication_platform.shared.models import Message, MessageType
from communication_platform.shared.database import get_db
from .database import MessageDB
from .models import IncomingMessageRequest

logger = logging.getLogger("twilio_monitor.handlers")

PHONE_REGEX = re.compile(r"^\+?[1-9]\d{1,14}$")


def validate_phone_number(phone: str) -> bool:
    """Validate phone number in E.164 format."""
    return bool(PHONE_REGEX.match(phone))


def sanitize_content(content: str) -> str:
    """Remove potentially harmful content (basic sanitizer)."""
    # Remove script tags and limit length
    sanitized = re.sub(r"<script.*?>.*?</script>", "", content, flags=re.IGNORECASE | re.DOTALL)
    return sanitized[:1600]


def store_message_in_db(message: Message, db: Session) -> MessageDB:
    """Store a Message in the database."""
    db_message = MessageDB(
        message_id=message.message_id,
        type=message.type.value,
        from_phone=message.from_phone,
        to_phone=message.to_phone,
        content=message.content,
        timestamp=datetime.utcfromtimestamp(message.timestamp),
        customer_id=message.customer_id,
        conversation_id=message.conversation_id,
        created_at=datetime.utcnow(),
    )
    db.add(db_message)
    db.commit()
    db.refresh(db_message)
    return db_message


async def process_incoming_message(request: IncomingMessageRequest, trace_id: UUID, db: Session) -> dict:
    """
    Process an incoming message: validate, sanitize, store, and return status.
    """
    try:
        if not validate_phone_number(request.from_phone):
            logger.error(f"[{trace_id}] Invalid from_phone: {request.from_phone}")
            return {"status": "error", "reason": "Invalid from_phone format"}
        if not validate_phone_number(request.to_phone):
            logger.error(f"[{trace_id}] Invalid to_phone: {request.to_phone}")
            return {"status": "error", "reason": "Invalid to_phone format"}

        sanitized_content = sanitize_content(request.content)
        now = datetime.utcnow().timestamp()
        message = Message(
            type=request.type,
            from_phone=request.from_phone,
            to_phone=request.to_phone,
            content=sanitized_content,
            timestamp=now,
        )
        db_message = store_message_in_db(message, db)
        logger.info(f"[{trace_id}] Stored message {db_message.message_id}")
        return {"message_id": str(db_message.message_id), "status": "received"}
    except Exception as e:
        logger.exception(f"[{trace_id}] Failed to process incoming message: {e}")
        return {"status": "error", "reason": str(e)} 