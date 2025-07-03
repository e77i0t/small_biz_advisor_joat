import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from communication_platform.shared import events
from uuid import uuid4
from datetime import datetime

@pytest.mark.parametrize("event_cls,expected_type", [
    (events.MessageReceivedEvent, events.EventType.MESSAGE_RECEIVED),
    (events.ConversationUpdatedEvent, events.EventType.CONVERSATION_UPDATED),
    (events.ConversationCategorizedEvent, events.EventType.CONVERSATION_CATEGORIZED),
    (events.MessageFlaggedEvent, events.EventType.MESSAGE_FLAGGED),
    (events.MessageSentEvent, events.EventType.MESSAGE_SENT),
    (events.CustomerCreatedEvent, events.EventType.CUSTOMER_CREATED),
])
def test_event_schema_and_serialization(event_cls, expected_type):
    event = event_cls(
        event_id=uuid4(),
        event_type=expected_type,
        timestamp=datetime.utcnow(),
        trace_id=uuid4(),
        source_service="test_service",
        payload={"foo": "bar"}
    )
    data = event.dict()
    assert data["event_type"] == expected_type
    assert data["payload"]["foo"] == "bar"
    # Test serialization
    json_str = event.json()
    assert "test_service" in json_str

# If routing key generation is implemented, test it here
# def test_routing_key_generation():
#     event = events.MessageReceivedEvent(...)
#     assert event.routing_key() == "expected.key" 