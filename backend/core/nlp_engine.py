import json
import os
import random
import string
from datetime import datetime
try:
    from thefuzz import process
except ImportError:
    process = None

from utils.logger import logger
import google.generativeai as genai
from config import Config

# Optional dependencies for "Industry Level" features
try:
    from googletrans import Translator
    from langdetect import detect
    HAS_TRANSLATION = True
except ImportError:
    HAS_TRANSLATION = False

try:
    import nltk
    from nltk.stem import WordNetLemmatizer
    # Try to download without blocking too long or just use if available
    # nltk.download('wordnet', quiet=True) # Removed to prevent hanging
    HAS_NLTK = True
except ImportError:
    HAS_NLTK = False

class NLPEngine:
    def __init__(self):
        logger.info("Initializing NLPEngine...")
        # Load intents from intents.json
        intents_path = os.path.join(os.path.dirname(__file__), 'intents.json')
        self.knowledge_base = {}
        
        self.lemmatizer = None
        if HAS_NLTK:
            logger.info("Checking NLTK...")
            try:
                self.lemmatizer = WordNetLemmatizer()
                # Test the lemmatizer to trigger any missing data errors
                self.lemmatizer.lemmatize("testing")
            except (LookupError, Exception):
                try:
                    logger.info("NLTK wordnet not found. Downloading...")
                    nltk.download('wordnet', quiet=True)
                    nltk.download('omw-1.4', quiet=True)
                    self.lemmatizer = WordNetLemmatizer()
                except Exception as e:
                    logger.warning(f"Failed to download NLTK data: {e}")
                    self.lemmatizer = None

        self.translator = None
        if HAS_TRANSLATION:
            logger.info("Checking Translator...")
            try:
                self.translator = Translator()
            except Exception as e:
                logger.warning(f"Failed to initialize translator: {e}")
                self.translator = None
        
        logger.info("Loading intents...")
        try:
            with open(intents_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.intents_data = data.get('intents', [])
                
            # THE PIVOT: BUILDING THE HASH MAP
            for intent in self.intents_data:
                for pattern in intent.get('patterns', []):
                    clean_pattern = self._clean_and_lemmatize(pattern)
                    self.knowledge_base[clean_pattern] = intent['tag']
            
            logger.info(f"Knowledge Base built with {len(self.knowledge_base)} patterns.")
        except Exception as e:
            logger.error(f"Error loading intents.json: {e}")
            self.intents_data = []

        self.session_contexts = {}

        # Setup Gemini AI Hybrid Fallback
        self.use_gemini = False
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_api_key_here":
            logger.info("Setting up Gemini...")
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                
                # List available models for debugging
                try:
                    all_available = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
                    available_models = [m.replace('models/', '') for m in all_available]
                    logger.info(f"Available Gemini models: {available_models}")
                except Exception as list_e:
                    logger.warning(f"Could not list models: {list_e}")
                    available_models = []

                # Preferred order (Newest first)
                preferred = [
                    'gemini-2.5-flash', 
                    'gemini-2.0-flash', 
                    'gemini-1.5-flash',
                    'gemini-flash-latest',
                    'gemini-pro'
                ]
                
                # Intersect preferred with available to find the best working model
                models_to_try = [m for m in preferred if m in available_models]
                # If no preferred models are available, just try any available ones
                if not models_to_try:
                    models_to_try = available_models

                for model_name in models_to_try:
                    try:
                        self.model = genai.GenerativeModel(model_name)
                        self.use_gemini = True
                        logger.info(f"Gemini AI Hybrid Fallback enabled using model: {model_name}")
                        break
                    except Exception as model_e:
                        logger.warning(f"Model {model_name} initialization failed: {model_e}")
            except Exception as e:
                logger.error(f"Failed to configure Gemini AI: {e}")
        logger.info("NLPEngine initialized.")

    def _clean_and_lemmatize(self, text):
        """Standardizes text by removing punctuation and lemmatizing words."""
        text = text.lower().strip()
        text = text.translate(str.maketrans('', '', string.punctuation))
        if self.lemmatizer:
            try:
                words = text.split()
                lemmatized_words = [self.lemmatizer.lemmatize(w) for w in words]
                return " ".join(lemmatized_words)
            except:
                pass
        return text

    def _process_dynamic_placeholders(self, text):
        """Replaces placeholders like {time} or {date} with actual values."""
        now = datetime.now()
        replacements = {
            "{time}": now.strftime("%I:%M %p"),
            "{date}": now.strftime("%B %d, %Y"),
            "{day}": now.strftime("%A")
        }
        for placeholder, value in replacements.items():
            text = text.replace(placeholder, value)
        return text

    def get_response(self, user_message, session_id="default"):
        # PHASE 0: MULTILINGUAL SUPPORT (Robustness: skip for very short strings or common English)
        original_lang = "en"
        processed_message = user_message
        
        # Common English words/greetings to avoid mis-detection
        common_en = ["hi", "hello", "hey", "how", "what", "who", "where", "why", "help", "thanks", "thank", "bye"]
        is_common_en = any(user_message.lower().startswith(w) for w in common_en)

        if HAS_TRANSLATION and self.translator and len(user_message.strip()) > 3 and not is_common_en:
            try:
                original_lang = detect(user_message)
                if original_lang != "en":
                    translation = self.translator.translate(user_message, dest='en')
                    processed_message = translation.text
                    logger.info(f"Translated '{user_message}' ({original_lang}) -> '{processed_message}'")
            except Exception as e:
                logger.warning(f"Translation/Detection failed: {e}")

        # PHASE 1: INPUT & SANITIZATION
        clean_input = self._clean_and_lemmatize(processed_message)
        
        # PHASE 2: CONTEXTUAL NESTED LOGIC
        context = self.session_contexts.get(session_id)
        if context == "awaiting_mood":
            self.session_contexts[session_id] = None
            if any(word in clean_input for word in ["good", "great", "fine", "happy", "well"]):
                resp = "That's wonderful to hear! I'm glad you're doing well. How else can Axiom AI help?"
                return {"text": self._translate_back(resp, original_lang), "source": "rule"}
            elif any(word in clean_input for word in ["bad", "sad", "not good", "tired", "unhappy"]):
                resp = "I'm sorry to hear that. I hope things get better soon! I'm here if you want to chat more about other things."
                return {"text": self._translate_back(resp, original_lang), "source": "rule"}

        # PHASE 3: EXACT MATCHING
        intent_tag = self.knowledge_base.get(clean_input)
        
        # Robustness Check: If we found a match in our English knowledge base, 
        # and the input is relatively short, trust that it is English.
        if intent_tag and original_lang != "en" and len(user_message.strip()) < 30:
            original_lang = "en"
            logger.info(f"Language override: Match found in English rules, resetting language to 'en'.")

        # PHASE 4: FUZZY MATCHING
        if not intent_tag and process:
            choices = list(self.knowledge_base.keys())
            if choices:
                best_match, score = process.extractOne(clean_input, choices)
                if score > 80:
                    intent_tag = self.knowledge_base[best_match]
                    logger.info(f"FUZZY MATCH: '{intent_tag}' (Score: {score})")
        
        if intent_tag:
            for intent in self.intents_data:
                if intent['tag'] == intent_tag:
                    response_text = random.choice(intent['responses'])
                    response_text = self._process_dynamic_placeholders(response_text)
                    
                    if intent_tag == "status":
                        self.session_contexts[session_id] = "awaiting_mood"
                        response_text += " How are *you* doing today?"
                    
                    final_resp = self._translate_back(response_text, original_lang)
                    return {"text": final_resp, "source": "rule"}
        
        # PHASE 5: HYBRID FALLBACK
        if self.use_gemini:
            try:
                prompt = (
                    "You are Axiom AI, a professional rule-based assistant. "
                    "Respond to this query concisely and maintain the persona: " + processed_message
                )
                response = self.model.generate_content(prompt)
                final_text = "*(Hybrid Mode: Rule mismatch, using Axiom-Cloud)*\n\n" + response.text
                return {"text": self._translate_back(final_text, original_lang), "source": "gemini"}
            except Exception as e:
                logger.error(f"Gemini AI Fallback failed: {e}")

        # PHASE 6: DEFAULT RESPONSE
        default_resp = "I apologize, but my current rule-set doesn't cover that specific query. Try asking about my features, the time, or say 'help' for guidance."
        return {"text": self._translate_back(default_resp, original_lang), "source": "error"}

    def _translate_back(self, text, lang):
        """Translates the response back to the user's original language."""
        if lang == "en" or not text or not HAS_TRANSLATION or not self.translator:
            return text
        try:
            translation = self.translator.translate(text, dest=lang)
            return translation.text
        except Exception as e:
            logger.warning(f"Translation back to {lang} failed: {e}")
            return text

    def start_loop(self):
        """The CLI Heartbeat loop."""
        print("\033[94m" + "="*50)
        print("   AXIOM AI: RULE-BASED ENGINE ONLINE")
        print("="*50 + "\033[0m")
        print("Type 'exit' or 'quit' to shut down.")
        session_id = "cli_session"
        while True:
            try:
                user_input = input("\033[92mYou:\033[0m ")
                if user_input.lower().strip() in ['exit', 'quit', 'bye']:
                    print("\033[94mAxiom AI:\033[0m Goodbye!")
                    break
                if not user_input.strip(): continue
                response = self.get_response(user_input, session_id)
                print(f"\033[94mAxiom AI [{response['source']}]:\033[0m {response['text']}")
            except KeyboardInterrupt: break
            except Exception as e: print(f"\033[91mError:\033[0m {e}")


