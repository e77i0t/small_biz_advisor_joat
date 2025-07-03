import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from communication_platform.services.twilio_monitor.main import app as twilio_app

def test_database_failure():
    client = TestClient(twilio_app)
    with patch("communication_platform.services.twilio_monitor.database.store_message", side_effect=Exception("DB fail")):
        payload = {"from": "+1234567890", "body": "fail"}
        response = client.post("/incoming", json=payload)
        assert response.status_code in (400, 500)

def test_event_publishing_failure():
    client = TestClient(twilio_app)
    with patch("communication_platform.shared.event_publisher.EventPublisher.publish", side_effect=Exception("Event fail")):
        payload = {"from": "+1234567890", "body": "fail event"}
        response = client.post("/incoming", json=payload)
        assert response.status_code in (400, 500) 