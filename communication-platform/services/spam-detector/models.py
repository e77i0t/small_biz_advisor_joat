from datetime import datetime
from enum import Enum
from typing import List
from pydantic import BaseModel
from ...shared.models import SpamEvaluation

class SpamEvaluationRequest(BaseModel):
    phone_number: str
    message: str
    timestamp: datetime

class Action(str, Enum):
    ALLOW = "allow"
    FLAG = "flag"
    BLOCK = "block"

class SpamEvaluationResponse(BaseModel):
    is_spam: bool
    score: float  # 0.0 - 1.0
    reasons: List[str]
    action: Action

class SpamRule(BaseModel):
    rule_type: str
    pattern: str
    weight: float
    description: str

class PhoneReputation(BaseModel):
    phone_number: str
    reputation_score: float
    last_checked: datetime
    source: str 