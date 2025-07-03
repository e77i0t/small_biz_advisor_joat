from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field
from communication_platform.shared.models import MessageType

class IncomingMessageRequest(BaseModel):
    type: MessageType = Field(..., description="Type of message (e.g., sms, call, voicemail, email)")
    from_phone: str = Field(..., alias="from", description="Sender's phone number in E.164 format")
    to_phone: str = Field(..., alias="to", description="Recipient's phone number in E.164 format")
    content: str = Field(..., description="Message content")
    media_urls: Optional[List[str]] = Field(None, description="List of media URLs attached to the message")

    class Config:
        allow_population_by_field_name = True
        json_schema_extra = {
            "examples": [
                {
                    "type": "sms",
                    "from": "+1234567890",
                    "to": "+1098765432",
                    "content": "Hello, this is a test message.",
                    "media_urls": ["https://example.com/image1.jpg"]
                }
            ]
        }

class MessageResponse(BaseModel):
    message_id: str = Field(..., description="Unique message identifier")
    status: str = Field(..., description="Status of the message (e.g., received, sent)")
    timestamp: datetime = Field(..., description="Timestamp of the message event (ISO 8601)")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "message_id": "abc123-def456",
                    "status": "received",
                    "timestamp": "2024-06-01T12:00:00Z"
                }
            ]
        }

class WebhookValidationRequest(BaseModel):
    signature: str = Field(..., description="Twilio X-Twilio-Signature header value")
    url: str = Field(..., description="Webhook endpoint URL")
    payload: str = Field(..., description="Raw request body or query string for validation")

    class Config:
        json_schema_extra = {
            "examples": [
                {
                    "signature": "abcdef1234567890",
                    "url": "https://yourdomain.com/webhook",
                    "payload": "body=...&from=...&to=..."
                }
            ]
        } 