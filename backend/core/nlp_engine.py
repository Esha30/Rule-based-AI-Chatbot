import json
import os
import random
from thefuzz import process
from utils.logger import logger
import google.generativeai as genai
from config import Config

class NLPEngine:
    def __init__(self):
        # Load intents from intents.json
        intents_path = os.path.join(os.path.dirname(__file__), 'intents.json')
        self.knowledge_base = {}
        try:
            with open(intents_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.intents_data = data.get('intents', [])
                
            # THE PIVOT: BUILDING THE HASH MAP (O(1) Lookup)
            for intent in self.intents_data:
                for pattern in intent.get('patterns', []):
                    clean_pattern = pattern.lower().strip()
                    self.knowledge_base[clean_pattern] = intent['tag']
            
            logger.info(f"Knowledge Base built with {len(self.knowledge_base)} patterns.")
        except Exception as e:
            logger.error(f"Error loading intents.json: {e}")
            self.intents_data = []

        # Setup Gemini AI Hybrid Fallback
        self.use_gemini = False
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_api_key_here":
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_gemini = True
                logger.info("Gemini AI Hybrid Fallback enabled.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")

    def get_response(self, user_message):
        # PHASE 1: INPUT & SANITIZATION (Advanced Cleaning)
        import string
        clean_input = user_message.lower().strip()
        # Remove all punctuation for maximum matching flexibility
        clean_input = clean_input.translate(str.maketrans('', '', string.punctuation))
        
        # PHASE 2: EXACT MATCHING (O(1) Speed)
        intent_tag = self.knowledge_base.get(clean_input)
        
        # PHASE 3: FUZZY MATCHING (Industry Standard Typo Tolerance)
        if not intent_tag:
            choices = list(self.knowledge_base.keys())
            best_match, score = process.extractOne(clean_input, choices)
            if score > 80: # 80% similarity threshold
                intent_tag = self.knowledge_base[best_match]
                logger.info(f"FUZZY MATCH FOUND: '{intent_tag}' (Score: {score}) for '{clean_input}'")
        
        if intent_tag:
            logger.info(f"MATCH FOUND: '{intent_tag}' for input '{clean_input}'")
            for intent in self.intents_data:
                if intent['tag'] == intent_tag:
                    return {
                        "text": random.choice(intent['responses']),
                        "source": "rule"
                    }
        
        # PHASE 4: HYBRID FALLBACK (Gemini AI)
        if self.use_gemini:
            try:
                logger.info(f"FALLING BACK TO GEMINI for: '{user_message}'")
                prompt = (
                    "You are Axiom AI, a professional assistant. Respond to this query concisely: " + user_message
                )
                response = self.model.generate_content(prompt)
                return {
                    "text": response.text,
                    "source": "gemini"
                }
            except Exception as e:
                logger.error(f"Gemini AI Fallback failed: {e}")

        return {
            "text": "I am a deterministic rule-based engine and I don't have a programmed response for that yet. How else can I help you?",
            "source": "error"
        }

    def start_loop(self):
        """
        THE HEARTBEAT: THE INFINITE LOOP
        Runs until the Kill Command is received.
        """
        print("--- Axiom AI Logic Engine Online ---")
        print("Type 'exit' or 'quit' to stop the engine.")
        
        while True:
            try:
                # 1. INPUT
                raw_input = input("You: ")
                
                # 2. THE KILL COMMAND (EXIT STRATEGY)
                if raw_input.lower().strip() in ['exit', 'quit', 'bye', 'goodbye']:
                    print("Axiom AI: Goodbye! (Engine Shutting Down)")
                    break
                
                # 3. PROCESS & OUTPUT
                response = self.get_response(raw_input)
                print(f"Axiom AI: {response}")
                
            except KeyboardInterrupt:
                print("\nEngine Interrupted. Shutting down.")
                break
            except Exception as e:
                print(f"Engine Error: {e}")

