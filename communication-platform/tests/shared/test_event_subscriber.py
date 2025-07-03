import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from unittest.mock import MagicMock, patch
from communication_platform.shared import event_subscriber, events
from uuid import uuid4
from datetime import datetime

@pytest.fixture
def subscriber():
    return event_subscriber.EventSubscriber()

@patch("communication_platform.shared.event_subscriber.EventSubscriber._consume")
def test_event_consumption(mock_consume, subscriber):
    subscriber.consume()
    mock_consume.assert_called_once()

@patch("communication_platform.shared.event_subscriber.EventSubscriber._register_handler")
def test_handler_registration(mock_register, subscriber):
    def handler(event):
        pass
    subscriber.register_handler(events.EventType.MESSAGE_RECEIVED, handler)
    mock_register.assert_called_once_with(events.EventType.MESSAGE_RECEIVED, handler)

@patch("communication_platform.shared.event_subscriber.EventSubscriber._consume", side_effect=Exception("fail"))
def test_event_consumption_error(mock_consume, subscriber):
    with pytest.raises(Exception):
        subscriber.consume() 