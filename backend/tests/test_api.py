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
    assert b'healthy' in rv.data

def test_chat_endpoint(client):
    payload = {
        "message": "hi",
        "session_id": "test-session"
    }
    rv = client.post('/chat', 
                     data=json.dumps(payload),
                     content_type='application/json')
    assert rv.status_code == 200
    data = json.loads(rv.data)
    assert "response" in data
    assert data["session_id"] == "test-session"
