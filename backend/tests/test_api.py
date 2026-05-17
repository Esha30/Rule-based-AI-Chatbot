import sys
import os
import pytest
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app

@pytest.fixture
def client():
    app = create_app()
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_health_check(client):
    rv = client.get('/health')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "healthy"
    assert "db_connected" in data

def test_status_endpoint(client):
    rv = client.get('/status')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "online"
    assert "database" in data
    assert "engine" in data
    assert "patterns_loaded" in data

def test_chat_endpoint(client):
    payload = {
        "message": "hello",
        "session_id": "test-session-123"
    }
    rv = client.post('/chat', 
                     data=json.dumps(payload),
                     content_type='application/json')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "response" in data
    assert data["session_id"] == "test-session-123"
    assert "source" in data

def test_feedback_endpoint(client):
    # First insert a message via /chat so it can find it to apply feedback
    payload_chat = {
        "message": "tell me a joke",
        "session_id": "test-session-feedback"
    }
    rv_chat = client.post('/chat', 
                          data=json.dumps(payload_chat),
                          content_type='application/json')
    assert rv_chat.status_code == 200
    
    payload_feedback = {
        "message": "tell me a joke",
        "session_id": "test-session-feedback",
        "feedback": "up"
    }
    rv_feedback = client.post('/feedback',
                              data=json.dumps(payload_feedback),
                              content_type='application/json')
    assert rv_feedback.status_code == 200
    data = json.loads(rv_feedback.data)
    assert data["status"] == "success"

def test_history_endpoint(client):
    # Send a message
    payload_chat = {
        "message": "who are you",
        "session_id": "test-session-history"
    }
    client.post('/chat', 
                data=json.dumps(payload_chat),
                content_type='application/json')
    
    # Check history
    rv = client.get('/history?session_id=test-session-history')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert len(data) > 0
    assert data[0]["message"] == "who are you"
    assert "response" in data[0]

def test_sessions_endpoint(client):
    # Retrieve all sessions
    rv = client.get('/sessions')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert isinstance(data, list)

def test_delete_session(client):
    # Send a message to create a session
    payload_chat = {
        "message": "temp session",
        "session_id": "test-session-delete"
    }
    client.post('/chat', 
                data=json.dumps(payload_chat),
                content_type='application/json')
    
    # Delete the session
    rv = client.delete('/sessions/test-session-delete')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert data["status"] == "success"

