import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import pytest
from unittest.mock import patch, MagicMock
from communication_platform.services.twilio_monitor import handlers

def test_store_message_success():
    with patch("communication_platform.services.twilio_monitor.database.store_message") as mock_store:
        mock_store.return_value = True
        result = handlers.store_message({"from": "+1234567890", "body": "Hello"})
        assert result is True

def test_store_message_failure():
    with patch("communication_platform.services.twilio_monitor.database.store_message", side_effect=Exception("fail")):
        with pytest.raises(Exception):
            handlers.store_message({"from": "+1234567890", "body": "Hello"}) 