from enum import Enum
from uuid import UUID
from datetime import datetime
from typing import Dict, Any
from pydantic import BaseModel, Field

class EventType(str, Enum):
    MESSAGE_RECEIVED = "MESSAGE_RECEIVED"
    CONVERSATION_UPDATED = "CONVERSATION_UPDATED"
    CONVERSATION_CATEGORIZED = "CONVERSATION_CATEGORIZED"
    MESSAGE_FLAGGED = "MESSAGE_FLAGGED"
    MESSAGE_SENT = "MESSAGE_SENT"
    CUSTOMER_CREATED = "CUSTOMER_CREATED"

class BaseEvent(BaseModel):
    event_id: UUID
    event_type: EventType
    timestamp: datetime
    trace_id: UUID
    source_service: str
    payload: Dict[str, Any]

class MessageReceivedEvent(BaseEvent):
    event_type: EventType = EventType.MESSAGE_RECEIVED
    # routing_key: "message.received.{message_type}.{customer_status}"

class ConversationUpdatedEvent(BaseEvent):
    event_type: EventType = EventType.CONVERSATION_UPDATED
    # routing_key: "conversation.updated.{action}"

class ConversationCategorizedEvent(BaseEvent):
    event_type: EventType = EventType.CONVERSATION_CATEGORIZED
    # routing_key: "conversation.categorized.{category}.{confidence_level}"

class MessageFlaggedEvent(BaseEvent):
    event_type: EventType = EventType.MESSAGE_FLAGGED
    # routing_key: "message.flagged.{action}.{score_range}"

class MessageSentEvent(BaseEvent):
    event_type: EventType = EventType.MESSAGE_SENT
    # routing_key: "message.sent.{method}.{status}"

class CustomerCreatedEvent(BaseEvent):
    event_type: EventType = EventType.CUSTOMER_CREATED
    # routing_key: "customer.created.{status}" 