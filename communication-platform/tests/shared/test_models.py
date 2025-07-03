import pytest
from pydantic import ValidationError
from communication_platform.shared import models, events
from uuid import uuid4
from datetime import datetime

# Test Customer model
def test_customer_model_valid():
    customer = models.Customer(id=1, name="Test", phone="+1234567890")
    assert customer.name == "Test"
    assert customer.phone == "+1234567890"

def test_customer_model_missing_field():
    with pytest.raises(ValidationError):
        models.Customer(id=1, name="Test")

# Test EventType enum
@pytest.mark.parametrize("event_type", list(events.EventType))
def test_event_type_enum(event_type):
    assert isinstance(event_type.value, str)

# Test BaseEvent and subclasses
@pytest.mark.parametrize("event_cls", [
    events.MessageReceivedEvent,
    events.ConversationUpdatedEvent,
    events.ConversationCategorizedEvent,
    events.MessageFlaggedEvent,
    events.MessageSentEvent,
    events.CustomerCreatedEvent,
])
def test_event_model_valid(event_cls):
    event = event_cls(
        event_id=uuid4(),
        event_type=event_cls.__fields__["event_type"].default,
        timestamp=datetime.utcnow(),
        trace_id=uuid4(),
        source_service="test_service",
        payload={"foo": "bar"}
    )
    assert event.event_type in events.EventType
    assert event.payload["foo"] == "bar"

def test_event_model_missing_field():
    with pytest.raises(ValidationError):
        events.BaseEvent(event_id=uuid4(), event_type=events.EventType.MESSAGE_RECEIVED, timestamp=datetime.utcnow(), trace_id=uuid4(), source_service="test_service") 