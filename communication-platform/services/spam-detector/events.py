from uuid import UUID
from typing import Any, Dict
from datetime import datetime
from .handlers import evaluate_spam, FLAG_THRESHOLD
from .models import SpamEvaluationResponse
# from ..shared.event_publisher import publish_event  # Uncomment and implement as needed
# from ..shared.event_subscriber import subscribe_event  # Uncomment and implement as needed

# Placeholder for event subscription (to be replaced with actual event bus logic)
def subscribe_to_message_received():
    # subscribe_event('message.received.*', handle_message_received)
    pass

async def handle_message_received(event_data: Dict[str, Any]):
    # Extract message data from event
    payload = event_data.get('payload', {})
    phone_number = payload.get('phone_number')
    message = payload.get('message')
    timestamp = payload.get('timestamp')
    message_id = payload.get('message_id')
    trace_id = event_data.get('trace_id')

    # Convert timestamp if needed
    if isinstance(timestamp, str):
        timestamp = datetime.fromisoformat(timestamp)
    if isinstance(trace_id, str):
        trace_id = UUID(trace_id)
    if isinstance(message_id, str):
        message_id = UUID(message_id)

    # Ensure required fields are present
    if trace_id is None or message_id is None:
        raise ValueError("trace_id and message_id are required and must not be None.")

    # Evaluate spam
    evaluation: SpamEvaluationResponse = await evaluate_spam(phone_number, message, timestamp, trace_id)

    # Only publish flagged events for scores above FLAG_THRESHOLD
    if evaluation.score >= FLAG_THRESHOLD:
        publish_message_flagged_event(evaluation, message_id, trace_id)


def publish_message_flagged_event(evaluation: SpamEvaluationResponse, message_id: UUID, trace_id: UUID):
    # Construct event payload
    event_payload = {
        "message_id": str(message_id),
        "is_spam": evaluation.is_spam,
        "score": evaluation.score,
        "reasons": evaluation.reasons,
        "action": evaluation.action.value,
        "trace_id": str(trace_id),
    }
    # Publish event (replace with actual event bus logic)
    # publish_event("message.flagged.spam", event_payload)
    print(f"Published message.flagged.spam event: {event_payload}")

# Subscribe to message.received.* routing key on startup (placeholder)
subscribe_to_message_received() 