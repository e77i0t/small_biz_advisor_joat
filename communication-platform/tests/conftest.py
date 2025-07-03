import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
import sys

# Ensure the communication-platform directory is in sys.path for imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

# --- 1. test_db fixture ---
@pytest.fixture(scope="session")
def test_db():
    from communication_platform.shared import database
    test_db_url = "sqlite:///./test.db"
    engine = create_engine(test_db_url, connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    database.Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()
    database.Base.metadata.drop_all(bind=engine)
    if os.path.exists("./test.db"):
        os.remove("./test.db")

# --- 2. mock_event_publisher fixture ---
@pytest.fixture
def mock_event_publisher():
    with patch("communication_platform.shared.event_publisher.EventPublisher") as MockPublisher:
        yield MockPublisher.return_value

# --- 3. mock_rabbitmq fixture ---
@pytest.fixture
def mock_rabbitmq():
    with patch("communication_platform.shared.event_subscriber.EventSubscriber") as MockSubscriber:
        yield MockSubscriber.return_value

# --- 4. Sample data fixtures ---
@pytest.fixture
def sample_message():
    return {
        "id": 1,
        "content": "Test message",
        "sender": "customer",
        "timestamp": "2024-01-01T12:00:00Z"
    }

@pytest.fixture
def sample_conversation():
    return {
        "id": 1,
        "customer_id": 1,
        "messages": [],
        "status": "open"
    }

@pytest.fixture
def sample_customer():
    return {
        "id": 1,
        "name": "Test Customer",
        "phone": "+1234567890"
    }

# --- 5. client fixture for each service ---
@pytest.fixture(params=[
    "classifier-agent", "conversation-grouper", "responder", "spam-detector", "twilio-monitor"
])
def client(request):
    service = request.param
    module_path = f"communication_platform.services.{service}.main"
    with patch("sys.argv", ["test"]):
        mod = __import__(module_path, fromlist=["app"])
        app = getattr(mod, "app", None)
        if app is None:
            pytest.skip(f"No FastAPI app found in {module_path}")
        with TestClient(app) as c:
            yield c

# --- 6. mock_openai_response fixture ---
@pytest.fixture
def mock_openai_response():
    with patch("openai.ChatCompletion.create") as mock_create:
        mock_create.return_value = {"choices": [{"message": {"content": "Test classification"}}]}
        yield mock_create

# --- 7. mock_twilio_client fixture ---
@pytest.fixture
def mock_twilio_client():
    with patch("twilio.rest.Client") as MockTwilio:
        yield MockTwilio.return_value 