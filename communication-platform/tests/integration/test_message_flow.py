import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from communication_platform.services.twilio_monitor.main import app as twilio_app

@pytest.fixture
def client():
    return TestClient(twilio_app)

def test_message_flow(client):
    payload = {"from": "+1234567890", "body": "Integration test"}
    with patch("communication_platform.services.twilio_monitor.database.store_message", return_value=True) as mock_store, \
         patch("communication_platform.shared.event_publisher.EventPublisher.publish") as mock_publish:
        response = client.post("/incoming", json=payload)
        assert response.status_code in (200, 201)
        mock_store.assert_called_once()
        mock_publish.assert_called_once() 