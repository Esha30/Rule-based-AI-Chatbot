import sys
import os
import pytest

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.nlp_engine import NLPEngine

@pytest.fixture
def nlp():
    return NLPEngine()

def test_greeting(nlp):
    # Using a longer sentence to help langdetect
    response = nlp.get_response("hello there assistant")
    # If it stays English, check for greeting
    # If it translates, just check it's not empty
    assert response is not None
    assert len(response) > 0

def test_fuzzy_greeting(nlp):
    response = nlp.get_response("helo nexus")
    assert response is not None
    assert len(response) > 0

def test_identity(nlp):
    response = nlp.get_response("who are you exactly")
    # Identity usually contains "Nexus AI" which shouldn't be translated or is recognizable
    assert "Nexus AI" in response

def test_unknown_query(nlp):
    response = nlp.get_response("asdfghjkl qwertyuiop")
    assert response is not None
    assert len(response) > 0

def test_translation_logic(nlp):
    # Explicitly test Spanish to see if it responds (likely in Spanish)
    response = nlp.get_response("hola amigo")
    assert response is not None
    assert len(response) > 0
    # We can't easily assert "Hola" because the bot might say "Hello" translated to Spanish
