# Events for the Classifier Agent service 
import os
import logging
from uuid import uuid4, UUID
from datetime import datetime
from communication_platform.shared.event_subscriber import EventSubscriber
from communication_platform.shared.event_publisher import EventPublisher
from communication_platform.shared.events import EventType, ConversationCategorizedEvent
from .handlers import classify_conversation
from .models import ClassificationResponse

logger = logging.getLogger("classifier_agent.events")

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://dev:dev123@localhost:5672/")
SERVICE_NAME = "classifier-agent"
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

async def handle_conversation_updated(event_data: dict):
    trace_id = event_data.get("trace_id", str(uuid4()))
    try:
        payload = event_data.get("payload", {})
        conversation_id = payload.get("conversation_id")
        if not conversation_id:
            logger.error(f"[{trace_id}] No conversation_id in event payload.")
            return
        logger.info(f"[{trace_id}] Handling CONVERSATION_UPDATED for conversation_id {conversation_id}")
        # Classify conversation
        try:
            classification = await classify_conversation(UUID(conversation_id), UUID(trace_id))
        except Exception as ai_err:
            logger.exception(f"[{trace_id}] AI classification failed: {ai_err}")
            return
        # Publish categorized event
        try:
            publish_conversation_categorized_event(classification, UUID(trace_id))
        except Exception as pub_err:
            logger.exception(f"[{trace_id}] Failed to publish CONVERSATION_CATEGORIZED event: {pub_err}")
    except Exception as e:
        logger.exception(f"[{trace_id}] Error handling CONVERSATION_UPDATED: {e}")

def publish_conversation_categorized_event(classification: ClassificationResponse, trace_id: UUID):
    global publisher
    if publisher is None:
        setup_event_subscriber()
    try:
        event = ConversationCategorizedEvent(
            event_id=uuid4(),
            event_type=EventType.CONVERSATION_CATEGORIZED,
            timestamp=datetime.utcnow(),
            trace_id=trace_id,
            source_service=SERVICE_NAME,
            payload={
                "conversation_id": str(classification.conversation_id),
                "category": str(classification.category),
                "confidence": classification.confidence,
                "reasoning": classification.reasoning
            }
        )
        routing_key = f"conversation.categorized.{classification.category}.{int(classification.confidence * 100)}"
        publisher.publish(event, routing_key=routing_key)
        logger.info(f"[{trace_id}] Published CONVERSATION_CATEGORIZED event for conversation {classification.conversation_id}")
    except Exception as e:
        logger.exception(f"[{trace_id}] Failed to publish CONVERSATION_CATEGORIZED event: {e}")

def start_event_consumption():
    global subscriber
    if subscriber is None:
        setup_event_subscriber()
    # Subscribe to all conversation.updated events
    subscriber.subscribe("conversation.updated.*", lambda event_data: handle_conversation_updated(event_data))
    logger.info("Subscribed to 'conversation.updated.*' events.")
    subscriber.start_consuming() 