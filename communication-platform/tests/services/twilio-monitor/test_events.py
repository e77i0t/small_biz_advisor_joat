import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import pytest
from unittest.mock import patch, MagicMock
from communication_platform.services.twilio_monitor import events

def test_event_publishing():
    with patch("communication_platform.shared.event_publisher.EventPublisher.publish") as mock_publish:
        event = MagicMock()
        events.publish_event(event)
        mock_publish.assert_called_once()

def test_event_consumption():
    with patch("communication_platform.shared.event_subscriber.EventSubscriber.consume") as mock_consume:
        events.consume_events()
        mock_consume.assert_called_once() 