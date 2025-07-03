from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
from uuid import UUID
from typing import List
from datetime import datetime
from ...shared.service_base import ServiceBase
from .models import SpamEvaluationRequest, SpamEvaluationResponse, SpamRule
from .handlers import evaluate_spam, check_phone_reputation, SPAM_KEYWORDS, SPAM_PATTERNS
from .events import handle_message_received, subscribe_to_message_received

service = ServiceBase("spam-detector", "0.1.0")
app = service.app

@app.on_event("startup")
def startup_event():
    # Start background event consumption
    subscribe_to_message_received()

@app.post("/evaluate", response_model=SpamEvaluationResponse)
async def evaluate(request: SpamEvaluationRequest):
    # Manual spam evaluation endpoint
    trace_id = UUID(int=0)  # Dummy trace_id for manual evaluation
    return await evaluate_spam(request.phone_number, request.message, request.timestamp, trace_id)

@app.get("/reputation/{phone_number}")
async def get_reputation(phone_number: str):
    score = await check_phone_reputation(phone_number)
    return {"phone_number": phone_number, "reputation_score": score}

class ReportRequest(BaseModel):
    phone_number: str
    reason: str

@app.post("/report")
async def report_spam(request: ReportRequest):
    # Placeholder: Store/report spam number (to be implemented)
    # TODO: Save report to database or notify admin
    return {"status": "reported", "phone_number": request.phone_number, "reason": request.reason}

@app.get("/rules", response_model=List[SpamRule])
def get_rules():
    # Return current spam detection rules (keywords and patterns)
    rules = []
    for keyword in SPAM_KEYWORDS:
        rules.append(SpamRule(rule_type="keyword", pattern=keyword, weight=0.2, description=f"Keyword: {keyword}"))
    for pattern in SPAM_PATTERNS:
        rules.append(SpamRule(rule_type="pattern", pattern=pattern.pattern, weight=0.2, description=f"Pattern: {pattern.pattern}"))
    return rules 