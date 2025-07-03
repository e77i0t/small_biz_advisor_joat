from typing import List, Optional
from uuid import UUID, uuid4
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ...shared.models import Message
from .models import GroupingResponse, ConversationSummary
from .database import ConversationDB, MessageDB
from ...shared.database import SessionLocal

GROUPING_WINDOW_HOURS = 2

async def group_messages(message_ids: List[UUID], trace_id: UUID) -> GroupingResponse:
    """
    Fetch messages, apply grouping, create/update conversation, return result.
    """
    with SessionLocal() as db:
        orm_messages = db.query(MessageDB).filter(MessageDB.message_id.in_(message_ids)).all()
        if not orm_messages:
            raise ValueError("No messages found for provided IDs")
        # Convert ORM to Pydantic Message models for grouping logic
        messages = [Message(
            message_id=m.message_id,
            type=m.type,
            **{"from": m.from_phone, "to": m.to_phone},
            content=m.content,
            timestamp=m.timestamp.timestamp() if isinstance(m.timestamp, datetime) else float(m.timestamp),
            customer_id=m.customer_id,
            conversation_id=m.conversation_id if isinstance(m.conversation_id, UUID) else uuid4()
        ) for m in orm_messages]
        if should_group_messages(messages):
            # Try to find existing conversation
            phone_number = messages[0].from_phone
            timestamp = datetime.utcfromtimestamp(messages[0].timestamp)
            conversation = find_existing_conversation(phone_number, timestamp, db)
            action = "updated" if conversation else "created"
            if not conversation:
                conversation = ConversationDB()
                db.add(conversation)
            for msg in orm_messages:
                conversation.add_message(msg)
            db.commit()
            conv_id = conversation.conversation_id
            if not isinstance(conv_id, UUID):
                conv_id = uuid4()
            return GroupingResponse(
                conversation_id=conv_id,
                action=action,
                message_count=conversation.get_messages().__len__()
            )
        else:
            return GroupingResponse(
                conversation_id=uuid4(),
                action="not_grouped",
                message_count=len(messages)
            )

def should_group_messages(messages: List[Message]) -> bool:
    """
    Group if all messages are within 2 hours, phone numbers match, and content is similar.
    """
    if not messages:
        return False
    # Time window check
    timestamps = [msg.timestamp for msg in messages]
    if max(timestamps) - min(timestamps) > GROUPING_WINDOW_HOURS * 3600:
        return False
    # Phone number check
    from_phones = {msg.from_phone for msg in messages}
    to_phones = {msg.to_phone for msg in messages}
    if len(from_phones) > 1 or len(to_phones) > 1:
        return False
    # Content similarity (basic keyword matching)
    keywords = set(messages[0].content.lower().split())
    for msg in messages[1:]:
        if not keywords.intersection(set(msg.content.lower().split())):
            return False
    return True

def create_conversation_summary(messages: List[Message]) -> ConversationSummary:
    """
    Create a simple summary and confidence score for a conversation.
    """
    if not messages:
        return ConversationSummary(conversation_id=uuid4(), summary="", confidence=0.0)
    summary = f"{len(messages)} messages between {messages[0].from_phone} and {messages[0].to_phone}."
    # Confidence: fraction of messages with overlapping keywords
    keywords = set(messages[0].content.lower().split())
    overlap = sum(1 for msg in messages if keywords.intersection(set(msg.content.lower().split())))
    confidence = overlap / len(messages)
    conv_id = messages[0].conversation_id
    if not isinstance(conv_id, UUID):
        conv_id = uuid4()
    return ConversationSummary(
        conversation_id=conv_id,
        summary=summary,
        confidence=confidence
    )

def find_existing_conversation(phone_number: str, timestamp: datetime, db: Session) -> Optional[ConversationDB]:
    """
    Find a conversation by phone number and time window.
    """
    window_start = timestamp - timedelta(hours=GROUPING_WINDOW_HOURS)
    window_end = timestamp + timedelta(hours=GROUPING_WINDOW_HOURS)
    return db.query(ConversationDB).join(ConversationDB.messages).filter(
        (MessageDB.from_phone == phone_number) |
        (MessageDB.to_phone == phone_number),
        ConversationDB.created_at >= window_start,
        ConversationDB.created_at <= window_end
    ).first() 