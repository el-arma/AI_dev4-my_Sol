from db import Base
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from main import app, get_db
from models import ConversationHistory
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from unittest.mock import patch


class FakeResult:
    def __init__(self, output):
        self.output = output

@pytest.fixture
def mock_agent():
    with patch("main.Agent_Thompson") as mock_agent:
        mock_agent.run_sync.return_value = FakeResult("mocked response")
        yield

TEST_DB = "sqlite:///./test_db.db"

# Load .env ONLY if running locally (safe fallback)
load_dotenv()

engine = create_engine(
    TEST_DB, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    autocommit=False
)

# --- DB utils ---

def fresh_test_db():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

@pytest.fixture #inject to test function
def setup_db():
    # Automatically reset the test database before each test.
    # This ensures full isolation between tests and prevents data leakage.
    fresh_test_db()

def get_test_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# Override dependency
app.dependency_overrides[get_db] = get_test_db

client = TestClient(app)

# --- Helpers ---

def send_message(session_id: str, msg: str):
    
    payload = {
        "sessionID": session_id,
        "msg": msg
    }

    return client.post("/api/v1/friendly-ear", json=payload)

def get_messages(session_id: str):

    db = TestingSessionLocal()

    try:
        return (
            db.query(ConversationHistory)
            .filter(ConversationHistory.session_id == session_id)
            .order_by(ConversationHistory.id)
            .all()
        )
    finally:
        db.close()

# --- Tests ---

def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == {"message": "Hello from GCP container! 🐳 "}


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

def test_ask_agent(setup_db, mock_agent):

    response = send_message("abc123", "hello")

    assert response.status_code == 200
    assert response.json() == {'msg': 'mocked response'}

def test_conversation_persistence_and_db(setup_db, mock_agent):

    response1 = send_message("abc123", "hello")
    assert response1.status_code == 200
    assert response1.json() == {'msg': 'mocked response'}

    response2 = send_message("abc123", "second hello")
    assert response2.status_code == 200
    assert response2.json() == {'msg': 'mocked response'}

    messages = get_messages("abc123")

    assert len(messages) == 4

    assert messages[0].role == "user"
    assert messages[0].message == "hello"

    assert messages[1].role == "agent"
    assert messages[1].message == "mocked response"

    assert messages[2].role == "user"
    assert messages[2].message == "second hello"

    assert messages[3].role == "agent"
    assert messages[3].message == "mocked response"