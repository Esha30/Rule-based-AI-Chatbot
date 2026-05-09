import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    PORT = int(os.environ.get("PORT", 5000))
    MONGODB_URI = os.environ.get("MONGODB_URI", "mongodb://localhost:27017/")
    DB_NAME = os.environ.get("DB_NAME", "chatbotDB")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
    DEBUG = True
