import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from unittest.mock import MagicMock, patch
from communication_platform.shared import event_publisher, events
from uuid import uuid4
from datetime import datetime

@pytest.fixture
def publisher():
    return event_publisher.EventPublisher()

@patch("communication_platform.shared.event_publisher.EventPublisher._publish")
def test_publish_event_success(mock_publish, publisher):
    event = events.MessageReceivedEvent(
        event_id=uuid4(),
        event_type=events.EventType.MESSAGE_RECEIVED,
        timestamp=datetime.utcnow(),
        trace_id=uuid4(),
        source_service="test_service",
        payload={"foo": "bar"}
    )
    publisher.publish(event)
    mock_publish.assert_called_once()

@patch("communication_platform.shared.event_publisher.EventPublisher._publish", side_effect=Exception("fail"))
def test_publish_event_error(mock_publish, publisher):
    event = events.MessageReceivedEvent(
        event_id=uuid4(),
        event_type=events.EventType.MESSAGE_RECEIVED,
        timestamp=datetime.utcnow(),
        trace_id=uuid4(),
        source_service="test_service",
        payload={"foo": "bar"}
    )
    with pytest.raises(Exception):
        publisher.publish(event)

# Add more tests for connection management if implemented 