import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

import pytest
from fastapi.testclient import TestClient
from communication_platform.services.twilio_monitor.main import app as twilio_app

@pytest.fixture(scope="module")
def client():
    return TestClient(twilio_app)

@pytest.fixture(scope="module")
def test_messages():
    return [
        {"from": f"+1234567{i:04d}", "body": f"Message {i}"} for i in range(1000)
    ]

def test_load_high_message_volume(client, test_messages, benchmark):
    def send_all():
        for msg in test_messages:
            client.post("/incoming", json=msg)
    benchmark(send_all) 