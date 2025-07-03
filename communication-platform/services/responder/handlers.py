# handlers.py for responder service 
from typing import Dict, Any, Optional
from uuid import UUID
from datetime import datetime, time
from pydantic import BaseModel
from .models import ResponseRequest, ResponseTemplate, AutoResponseRule, DeliveryStatus, DeliveryStatusEnum
from ...shared.models import Conversation, ConversationCategory
import os
import logging
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

# --- Configuration ---
BUSINESS_HOURS = {
    "start": time(9, 0),   # 9:00 AM
    "end": time(17, 0),    # 5:00 PM
    "timezone": "America/New_York"
}

AUTO_RESPONSE_RULES = [
    AutoResponseRule(
        trigger_category=ConversationCategory.new_lead,
        conditions={},
        template_id="welcome_new_lead",
        delay_seconds=0
    ),
    # Add more rules as needed
]

TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_PHONE_NUMBER = os.getenv("TWILIO_PHONE_NUMBER")

twilio_client = None
if TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN:
    twilio_client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
else:
    logging.warning("Twilio credentials not set. SMS sending will not work.")

# --- Handlers ---
async def send_automated_response(conversation_id: UUID, category: ConversationCategory, trace_id: UUID):
    # Fetch conversation (placeholder: should query DB)
    conversation = Conversation(
        conversation_id=conversation_id,
        message_ids=[],
        created_at=datetime.now().timestamp(),
        updated_at=datetime.now().timestamp(),
        confidence=1.0
    )
    if not should_auto_respond(category, conversation):
        return None
    rule = next((r for r in AUTO_RESPONSE_RULES if r.trigger_category == category), None)
    if not rule:
        return None
    template = get_template_by_id(rule.template_id)
    if not template:
        return None
    context = get_business_context()
    rendered_content = render_template(template.template_id, context)
    delivery = await send_sms_via_twilio(to="+1234567890", content=rendered_content)  # Replace with actual recipient
    # Track delivery status (placeholder)
    return delivery

async def send_sms_via_twilio(to: str, content: str) -> DeliveryStatus:
    import uuid
    from datetime import datetime
    if not twilio_client:
        logging.error("Twilio client not initialized. Cannot send SMS.")
        return DeliveryStatus(
            message_id=uuid.uuid4(),
            status=DeliveryStatusEnum.FAILED,
            delivered_at=datetime.now(),
            error_message="Twilio client not initialized."
        )
    try:
        message = twilio_client.messages.create(
            to=to,
            from_=TWILIO_PHONE_NUMBER,
            body=content
        )
        logging.info(f"Sent SMS to {to} via Twilio. SID: {message.sid}, Status: {message.status}")
        return DeliveryStatus(
            message_id=uuid.UUID(message.sid.ljust(32, '0')[:32]),  # Fake UUID from SID for tracking
            status=DeliveryStatusEnum.DELIVERED if message.status == "sent" else DeliveryStatusEnum.PENDING,
            delivered_at=datetime.now(),
            error_message=None
        )
    except TwilioRestException as e:
        logging.error(f"Twilio error sending SMS to {to}: {e}")
        return DeliveryStatus(
            message_id=uuid.uuid4(),
            status=DeliveryStatusEnum.FAILED,
            delivered_at=datetime.now(),
            error_message=str(e)
        )
    except Exception as e:
        logging.error(f"Unexpected error sending SMS to {to}: {e}")
        return DeliveryStatus(
            message_id=uuid.uuid4(),
            status=DeliveryStatusEnum.FAILED,
            delivered_at=datetime.now(),
            error_message=str(e)
        )

def render_template(template_id: str, context: dict) -> str:
    template = get_template_by_id(template_id)
    if not template:
        return ""
    return template.content.format(**context)

def should_auto_respond(category: ConversationCategory, conversation: Conversation) -> bool:
    # Example: Only auto-respond during business hours
    now = datetime.now().time()
    if BUSINESS_HOURS["start"] <= now <= BUSINESS_HOURS["end"]:
        return any(r.trigger_category == category for r in AUTO_RESPONSE_RULES)
    return False

def get_business_context() -> Dict[str, Any]:
    return {
        "business_name": "Small Biz Advisor",
        "contact_phone": "+1234567890",
        "contact_email": "info@smallbizadvisor.com",
        "hours": f"{BUSINESS_HOURS['start'].strftime('%H:%M')} - {BUSINESS_HOURS['end'].strftime('%H:%M')}"
    }

def get_template_by_id(template_id: str) -> Optional[ResponseTemplate]:
    # Placeholder: In real implementation, fetch from DB or file
    templates = {
        "welcome_new_lead": ResponseTemplate(
            template_id="welcome_new_lead",
            name="Welcome New Lead",
            content="Hello, thank you for reaching out to {business_name}! We will contact you during our business hours: {hours}.",
            category="new_lead",
            variables=["business_name", "hours"]
        )
    }
    return templates.get(template_id) 