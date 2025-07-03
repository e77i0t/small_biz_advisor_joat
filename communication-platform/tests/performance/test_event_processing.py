import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from unittest.mock import patch, MagicMock
from communication_platform.shared import event_publisher, event_subscriber, events
from uuid import uuid4
from datetime import datetime

@pytest.fixture(scope="module")
def test_events():
    return [
        events.MessageReceivedEvent(
            event_id=uuid4(),
            event_type=events.EventType.MESSAGE_RECEIVED,
            timestamp=datetime.utcnow(),
            trace_id=uuid4(),
            source_service="twilio-monitor",
            payload={"foo": f"bar{i}"}
        ) for i in range(1000)
    ]

def test_event_processing_speed(test_events, benchmark):
    with patch.object(event_publisher.EventPublisher, "publish", return_value=None) as mock_publish:
        def publish_all():
            pub = event_publisher.EventPublisher()
            for event in test_events:
                pub.publish(event)
        benchmark(publish_all)

    with patch.object(event_subscriber.EventSubscriber, "consume", return_value=None) as mock_consume:
        def consume_all():
            sub = event_subscriber.EventSubscriber()
            for _ in test_events:
                sub.consume()
        benchmark(consume_all) 