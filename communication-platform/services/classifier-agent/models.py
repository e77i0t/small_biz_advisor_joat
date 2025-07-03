# Models for the Classifier Agent service 
from typing import Optional, Dict
from uuid import UUID
from pydantic import BaseModel
from ...shared.models import ConversationCategory

class ClassificationRequest(BaseModel):
    conversation_id: UUID
    text: Optional[str] = None
    context: Optional[Dict] = None

class ClassificationResponse(BaseModel):
    conversation_id: UUID
    category: ConversationCategory
    confidence: float
    reasoning: str

class AIClassificationResult(BaseModel):
    category: str
    confidence: float
    reasoning: str
    model_used: str

class RuleBasedResult(BaseModel):
    category: str
    confidence: float
    reasoning: str 