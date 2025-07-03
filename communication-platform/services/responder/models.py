# models.py for responder service 
from pydantic import BaseModel, Field
from typing import Optional, Dict, List, Any
from uuid import UUID
from datetime import datetime
from enum import Enum
from ...shared.models import ConversationCategory

class ResponseRequest(BaseModel):
    to: str
    content: str
    template_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None

class ResponseTemplate(BaseModel):
    template_id: str
    name: str
    content: str
    category: str
    variables: List[str]

class AutoResponseRule(BaseModel):
    trigger_category: ConversationCategory
    conditions: Dict[str, Any]
    template_id: str
    delay_seconds: int

class DeliveryStatusEnum(str, Enum):
    PENDING = "pending"
    DELIVERED = "delivered"
    FAILED = "failed"

class DeliveryStatus(BaseModel):
    message_id: UUID
    status: DeliveryStatusEnum
    delivered_at: datetime
    error_message: Optional[str] = None 