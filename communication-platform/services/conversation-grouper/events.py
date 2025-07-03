import os
import logging
from uuid import uuid4, UUID
from datetime import datetime
from ...shared.event_subscriber import EventSubscriber
from ...shared.event_publisher import EventPublisher
from ...shared.events import EventType, MessageReceivedEvent, ConversationUpdatedEvent
from ...shared.models import Conversation
from .handlers import group_messages

logger = logging.getLogger("conversation_grouper.events")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://dev:dev123@localhost:5672/")
SERVICE_NAME = "conversation-grouper"
EXCHANGE_NAME = "communication_platform"

subscriber = None
publisher = None

def setup_event_subscriber():
    global subscriber, publisher
    if subscriber is None:
        subscriber = EventSubscriber(RABBITMQ_URL, SERVICE_NAME, EXCHANGE_NAME)
    if publisher is None:
        publisher = EventPublisher(RABBITMQ_URL, EXCHANGE_NAME)
    logger.info("Event subscriber and publisher set up.")

async def handle_message_received(event_data: dict):
    trace_id = event_data.get("trace_id", str(uuid4()))
    try:
        payload = event_data.get("payload", {})
        message_id = payload.get("message_id")
        if not message_id:
            logger.error(f"[{trace_id}] No message_id in event payload.")
            return
        logger.info(f"[{trace_id}] Handling MESSAGE_RECEIVED for message_id {message_id}")
        # Group messages (for demo, just group this single message)
        response = await group_messages([UUID(message_id)], UUID(trace_id))
        logger.info(f"[{trace_id}] Grouped into conversation {response.conversation_id} (action: {response.action})")
        # Publish conversation updated event
        publish_conversation_updated_event(response.conversation_id, response.action, UUID(trace_id))
    except Exception as e:
        logger.exception(f"[{trace_id}] Error handling MESSAGE_RECEIVED: {e}")

def publish_conversation_updated_event(conversation_id: UUID, action: str, trace_id: UUID):
    global publisher
    if publisher is None:
        setup_event_subscriber()
    try:
        event = ConversationUpdatedEvent(
            event_id=uuid4(),
            event_type=EventType.CONVERSATION_UPDATED,
            timestamp=datetime.utcnow(),
            trace_id=trace_id,
            source_service=SERVICE_NAME,
            payload={
                "conversation_id": str(conversation_id),
                "action": action
            }
        )
        publisher.publish(event, routing_key=f"conversation.updated.{action}")
        logger.info(f"[{trace_id}] Published CONVERSATION_UPDATED event for conversation {conversation_id}")
    except Exception as e:
        logger.exception(f"[{trace_id}] Failed to publish CONVERSATION_UPDATED event: {e}")

def start_event_consumption():
    global subscriber
    if subscriber is None:
        setup_event_subscriber()
    # Subscribe to all message.received events
    subscriber.subscribe("message.received.*", lambda event_data: handle_message_received(event_data))
    logger.info("Subscribed to 'message.received.*' events.")
    subscriber.start_consuming() 