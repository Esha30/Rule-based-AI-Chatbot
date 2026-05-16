import sys
import os
import pytest
from datetime import datetime

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nlp_engine import NLPEngine

@pytest.fixture
def nlp():
    return NLPEngine()

def test_greeting(nlp):
    response = nlp.get_response("Hello there")
    assert "Axiom AI" in response["text"]
    assert response["source"] == "rule"

def test_fuzzy_greeting(nlp):
    # Test typo tolerance
    response = nlp.get_response("helo axom")
    assert "Axiom AI" in response["text"]
    assert response["source"] == "rule"

def test_identity(nlp):
    response = nlp.get_response("who are you")
    assert "Axiom AI" in response["text"]
    assert "rule-based" in response["text"].lower()

def test_time_dynamic(nlp):
    response = nlp.get_response("what time is it")
    current_time = datetime.now().strftime("%I:%M %p")
    # We check if the response contains the hour part at least, 
    # to avoid minute mismatch if it ticks over during test
    assert current_time.split(":")[0] in response["text"]

def test_contextual_flow(nlp):
    # Step 1: Ask how it is
    resp1 = nlp.get_response("how are you", session_id="test_sess")
    assert "How are you doing today?" in resp1["text"]
    
    # Step 2: Answer positively
    resp2 = nlp.get_response("I am feeling great", session_id="test_sess")
    assert "wonderful to hear" in resp2["text"]
    assert resp2["source"] == "rule"

def test_unknown_query(nlp):
    response = nlp.get_response("asdfghjkl qwertyuiop")
    assert "apologize" in response["text"]
    assert response["source"] == "error"
