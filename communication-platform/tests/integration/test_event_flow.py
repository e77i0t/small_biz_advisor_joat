import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import patch, MagicMock
from communication_platform.shared import event_publisher, event_subscriber, events
from uuid import uuid4
from datetime import datetime

def test_event_publishing_and_consumption():
    event = events.MessageReceivedEvent(
        event_id=uuid4(),
        event_type=events.EventType.MESSAGE_RECEIVED,
        timestamp=datetime.utcnow(),
        trace_id=uuid4(),
        source_service="twilio-monitor",
        payload={"foo": "bar"}
    )
    with patch.object(event_publisher.EventPublisher, "publish") as mock_publish, \
         patch.object(event_subscriber.EventSubscriber, "consume") as mock_consume:
        publisher = event_publisher.EventPublisher()
        subscriber = event_subscriber.EventSubscriber()
        publisher.publish(event)
        mock_publish.assert_called_once_with(event)
        subscriber.consume()
        mock_consume.assert_called_once() 