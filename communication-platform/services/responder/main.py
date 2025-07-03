from fastapi import Request, BackgroundTasks, HTTPException
from typing import List, Dict, Any
from uuid import UUID
from .handlers import (
    ResponseRequest, ResponseTemplate, AutoResponseRule, AUTO_RESPONSE_RULES,
    get_template_by_id, render_template, BUSINESS_HOURS
)
from .events import subscribe_to_events
from ...shared.service_base import ServiceBase
import os
import glob

service = ServiceBase("responder", version="1.0.0")
app = service.app

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

def list_templates() -> List[Dict[str, Any]]:
    templates = []
    for path in glob.glob(os.path.join(TEMPLATES_DIR, "*.txt")):
        with open(path, "r") as f:
            content = f.read()
        template_id = os.path.splitext(os.path.basename(path))[0]
        templates.append({
            "template_id": template_id,
            "content": content
        })
    return templates

@app.post("/reply")
async def manual_reply(request: ResponseRequest):
    # Implement manual reply logic (send SMS, etc.)
    # For now, just simulate sending
    from .handlers import send_sms_via_twilio
    delivery = await send_sms_via_twilio(request.to, request.content)
    return {"status": delivery.status, "message_id": delivery.message_id}

@app.get("/templates")
def get_templates():
    return list_templates()

@app.post("/templates")
def create_or_update_template(template: ResponseTemplate):
    path = os.path.join(TEMPLATES_DIR, f"{template.template_id}.txt")
    with open(path, "w") as f:
        f.write(template.content)
    return {"status": "updated", "template_id": template.template_id}

@app.get("/rules")
def get_rules():
    return [rule.dict() for rule in AUTO_RESPONSE_RULES]

@app.put("/rules")
def update_rules(rules: List[AutoResponseRule]):
    global AUTO_RESPONSE_RULES
    AUTO_RESPONSE_RULES = rules
    return {"status": "updated", "count": len(rules)}

@app.on_event("startup")
def start_event_consumption():
    # Start background event consumption
    import threading
    t = threading.Thread(target=subscribe_to_events, daemon=True)
    t.start() 