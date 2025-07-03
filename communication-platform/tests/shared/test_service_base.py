import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..')))

import pytest
from communication_platform.shared import service_base
from fastapi.testclient import TestClient
from fastapi import FastAPI

class DummyService(service_base.ServiceBase):
    def __init__(self):
        super().__init__(service_name="dummy", version="0.1")

@pytest.fixture
def app():
    service = DummyService()
    return service.app

def test_health_check(app):
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"

# Add more tests for middleware if custom middleware is implemented 