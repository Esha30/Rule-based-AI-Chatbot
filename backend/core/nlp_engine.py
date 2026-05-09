import nltk
from nltk.tokenize import word_tokenize
import json
import os
import random
from thefuzz import fuzz
from utils.logger import logger
import google.generativeai as genai
from googletrans import Translator
from langdetect import detect, detect_langs, DetectorFactory
import sys

# For consistent language detection
DetectorFactory.seed = 0

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config

# Download required NLTK data
nltk.download('punkt', quiet=True)
nltk.download('punkt_tab', quiet=True)

class NLPEngine:
    def __init__(self):
        # Load intents from intents.json
        intents_path = os.path.join(os.path.dirname(__file__), 'intents.json')
        try:
            with open(intents_path, 'r', encoding='utf-8') as f:
                self.intents = json.load(f)
            logger.info("Successfully loaded intents.json")
        except Exception as e:
            logger.error(f"Error loading intents.json: {e}")
            self.intents = {"intents": []}

        # Setup Gemini
        self.use_gemini = False
        if Config.GEMINI_API_KEY and Config.GEMINI_API_KEY != "your_api_key_here":
            try:
                genai.configure(api_key=Config.GEMINI_API_KEY)
                self.model = genai.GenerativeModel('gemini-1.5-flash')
                self.use_gemini = True
                logger.info("Gemini AI fallback enabled.")
            except Exception as e:
                logger.error(f"Failed to initialize Gemini AI: {e}")
        
        # Setup Translator
        self.translator = Translator()

    def get_response(self, user_message):
        user_lang = 'en'
        try:
            # Common greeting patterns across supported languages
            en_greetings = {'hi', 'hello', 'hey', 'hy', 'yo', 'sup', 'howdy', 'greetings', 'tell', 'me', 'a', 'joke', 'what', 'is', 'how', 'who', 'where', 'when', 'why', 'can', 'you', 'help'}
            es_greetings = {'hola', 'como', 'estas', 'buenos', 'dias'}
            
            words = user_message.lower().split()
            
            # Direct mapping for very short, common greetings
            if len(words) <= 3:
                if any(w in en_greetings for w in words):
                    user_lang = 'en'
                    logger.info(f"Common English pattern detected.")
                elif any(w in es_greetings for w in words):
                    user_lang = 'es'
                    logger.info(f"Common Spanish pattern detected.")
                else:
                    # Only do complex detection if not in common lists
                    langs = detect_langs(user_message)
                    top_lang = langs[0]
                    # Be extremely skeptical of rare languages for short strings
                    if top_lang.lang in ['cy', 'fi', 'vi'] and top_lang.prob < 0.999:
                        user_lang = 'en'
                    elif top_lang.prob > 0.99: # High bar for short strings
                        user_lang = top_lang.lang
                    else:
                        user_lang = 'en'
            else:
                # For longer messages, use standard detection
                langs = detect_langs(user_message)
                top_lang = langs[0]
                if top_lang.lang != 'en' and top_lang.prob > 0.90:
                    user_lang = top_lang.lang
                else:
                    user_lang = 'en'
            
            logger.info(f"Final detected language: {user_lang}")
        except Exception as e:
            logger.error(f"Language detection failed: {e}")
            user_lang = 'en'

        # If not English, translate to English for processing
        processing_message = user_message
        if user_lang != 'en':
            try:
                translation = self.translator.translate(user_message, dest='en')
                processing_message = translation.text
                logger.info(f"Translated '{user_message}' to '{processing_message}'")
            except Exception as e:
                logger.error(f"Translation to English failed: {e}")

        processing_message_lower = processing_message.lower()
        
        try:
            tokens = word_tokenize(processing_message_lower)
        except LookupError:
            tokens = processing_message_lower.split()
            
        highest_score = 0
        best_intent = None

        # Check for intent matches using fuzzy matching
        for intent in self.intents.get('intents', []):
            for pattern in intent.get('patterns', []):
                score = fuzz.token_set_ratio(processing_message_lower, pattern.lower())
                if score > highest_score:
                    highest_score = score
                    best_intent = intent

        final_response = ""
        # If we have a high confidence match
        if highest_score > 75 and best_intent:
            logger.info(f"Matched intent '{best_intent['tag']}' with score {highest_score}")
            final_response = random.choice(best_intent['responses'])
        
        # Fallback to Gemini if confidence is low
        elif self.use_gemini:
            try:
                logger.info(f"Low confidence ({highest_score}). Falling back to Gemini AI.")
                response = self.model.generate_content(
                    f"You are Nexus AI, a professional conversational assistant. Answer this user query concisely. Respond in the original language if it's not English: {user_message}"
                )
                return response.text
            except Exception as e:
                logger.error(f"Gemini AI generation failed: {e}")
                final_response = "Sorry, I don't quite understand that."
        else:
            final_response = "Sorry, I don't quite understand that. I'm continually learning, but right now I mainly handle greetings, introductions, and basic questions."

        # Translate response back to user's language if necessary
        if user_lang != 'en' and final_response:
            try:
                translated_resp = self.translator.translate(final_response, dest=user_lang)
                logger.info(f"Translated response back to {user_lang}")
                return translated_resp.text
            except Exception as e:
                logger.error(f"Translation back to {user_lang} failed: {e}")
        
        return final_response
