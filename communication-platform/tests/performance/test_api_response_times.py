import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi.testclient import TestClient
from communication_platform.services.twilio_monitor.main import app as twilio_app

@pytest.fixture(scope="module")
def client():
    return TestClient(twilio_app)

def test_api_response_time(client, benchmark):
    payload = {"from": "+1234567890", "body": "Performance test"}
    def post_once():
        client.post("/incoming", json=payload)
    benchmark(post_once) 