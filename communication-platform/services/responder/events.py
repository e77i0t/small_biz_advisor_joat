# events.py for responder service 
from uuid import UUID, uuid4
from datetime import datetime
from typing import Any, Dict
import os
from ...shared.events import EventType, MessageSentEvent, ConversationCategorizedEvent
from ...shared.event_publisher import EventPublisher
from ...shared.event_subscriber import EventSubscriber
from .handlers import send_automated_response

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/")
SERVICE_NAME = "responder"
EXCHANGE_NAME = "communication_platform"

publisher = EventPublisher(RABBITMQ_URL, EXCHANGE_NAME)
subscriber = EventSubscriber(RABBITMQ_URL, SERVICE_NAME, EXCHANGE_NAME)

def publish_message_sent_event(message_id: UUID, to: str, content: str, method: str, status: str, trace_id: UUID):
    event = MessageSentEvent(
        event_id=uuid4(),
        event_type=EventType.MESSAGE_SENT,
        timestamp=datetime.now(),
        trace_id=trace_id,
        source_service=SERVICE_NAME,
        payload={
            "message_id": str(message_id),
            "to": to,
            "content": content,
            "method": method,
            "status": status
        }
    )
    publisher.publish(event, routing_key=f"message.sent.{method}.{status}")

async def handle_conversation_categorized(event_data: Dict[str, Any]):
    conversation_id = UUID(event_data["payload"]["conversation_id"])
    category = event_data["payload"].get("category")
    trace_id = UUID(event_data["trace_id"])
    # Call send_automated_response
    delivery = await send_automated_response(conversation_id, category, trace_id)
    if delivery:
        publish_message_sent_event(
            message_id=delivery.message_id,
            to=event_data["payload"].get("to", ""),
            content=delivery.status.value,  # Placeholder, should be actual content
            method="sms",
            status=delivery.status.value,
            trace_id=trace_id
        )

def handle_missed_call(event_data: Dict[str, Any]):
    # Extract info and send missed call response (sync for now)
    # You may want to make this async if your handler supports it
    pass  # Implement as needed

def subscribe_to_events():
    subscriber.subscribe("conversation.categorized.*", lambda event_data: handle_conversation_categorized(event_data))
    subscriber.subscribe("call.missed", lambda event_data: handle_missed_call(event_data)) 