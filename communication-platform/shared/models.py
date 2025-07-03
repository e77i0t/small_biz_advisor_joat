from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4
from pydantic import BaseModel, Field, EmailStr, constr

"""Shared Pydantic models and enums for the communication platform."""

# 1. MessageType enum
class MessageType(str, Enum):
    """Type of message in the platform."""
    sms = "sms"
    call = "call"
    voicemail = "voicemail"
    email = "email"

# 2. ConversationCategory enum
class ConversationCategory(str, Enum):
    """Category of conversation."""
    new_lead = "new_lead"
    quote_request = "quote_request"
    status_update = "status_update"
    reminder = "reminder"
    spam = "spam"
    support = "support"
    other = "other"

# 6. SpamAction enum (for SpamEvaluation)
class SpamAction(str, Enum):
    """Action to take for spam evaluation."""
    allow = "allow"
    flag = "flag"
    block = "block"

# 3. Message model
class Message(BaseModel):
    """A message sent or received in the platform."""
    message_id: UUID = Field(default_factory=uuid4)
    type: MessageType
    from_phone: constr(regex=r"^\+?[1-9]\d{1,14}$") = Field(..., alias="from")
    to_phone: constr(regex=r"^\+?[1-9]\d{1,14}$") = Field(..., alias="to")
    content: constr(max_length=1600)
    timestamp: float
    customer_id: Optional[UUID] = None
    conversation_id: Optional[UUID] = None

    class Config:
        allow_population_by_field_name = True

# 4. Conversation model
class Conversation(BaseModel):
    """A conversation consisting of multiple messages."""
    conversation_id: UUID = Field(default_factory=uuid4)
    message_ids: List[UUID]
    summary: Optional[constr(max_length=500)] = None
    category: Optional[ConversationCategory] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    customer_id: Optional[UUID] = None
    created_at: float
    updated_at: float

# 5. Customer model
class Customer(BaseModel):
    """A customer in the platform."""
    customer_id: UUID = Field(default_factory=uuid4)
    name: constr(max_length=100)
    phone: constr(regex=r"^\+?[1-9]\d{1,14}$")
    email: Optional[EmailStr] = None
    status: str = Field(default="trial")
    business_type: Optional[constr(max_length=50)] = None

# 6. SpamEvaluation model
class SpamEvaluation(BaseModel):
    """Spam evaluation result for a message or conversation."""
    is_spam: bool
    score: float = Field(..., ge=0.0, le=1.0)
    reasons: List[str]
    action: SpamAction 