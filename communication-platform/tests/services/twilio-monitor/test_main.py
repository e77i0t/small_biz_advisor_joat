import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..')))

import pytest
from fastapi.testclient import TestClient
from communication_platform.services.twilio_monitor.main import app

@pytest.fixture
def client():
    return TestClient(app)

def test_post_incoming_valid(client):
    payload = {"from": "+1234567890", "body": "Hello"}
    response = client.post("/incoming", json=payload)
    assert response.status_code in (200, 201)
    assert "message" in response.json() or "status" in response.json()

def test_post_incoming_invalid(client):
    payload = {"from": "notaphone", "body": ""}
    response = client.post("/incoming", json=payload)
    assert response.status_code in (400, 422)

def test_post_incoming_missing_fields(client):
    payload = {"body": "Hello"}
    response = client.post("/incoming", json=payload)
    assert response.status_code in (400, 422) 