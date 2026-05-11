import sys
import os

# Add backend to path relative to this file
backend_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'backend')
if backend_path not in sys.path:
    sys.path.append(backend_path)

from core.nlp_engine import NLPEngine
from dotenv import load_dotenv

# Load environment variables (for Gemini fallback if needed)
load_dotenv(dotenv_path=os.path.join('backend', '.env'))

def main():
    """
    STAKEHOLDER REQUIREMENT: THE HEARTBEAT
    A continuous digital loop that simulates human interaction.
    """
    engine = NLPEngine()
    engine.start_loop()

if __name__ == "__main__":
    main()
