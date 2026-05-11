import json
from pymongo import MongoClient
import sys
import os
from datetime import datetime

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from utils.logger import logger

class MongoDB:
    client = None
    db = None
    available = False
    LOCAL_STORAGE_PATH = os.path.join(os.path.dirname(__file__), "local_history.json")

    @classmethod
    def connect(cls):
        try:
            cls.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=2000)
            cls.db = cls.client[Config.DB_NAME]
            cls.db.command("ping")
            cls.available = True
            logger.info("Successfully connected to MongoDB Atlas.")
        except Exception as e:
            logger.error(f"MongoDB connection failed. Using Local JSON Fallback. Error: {e}")
            cls.available = False
            # Ensure local storage file exists
            if not os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'w') as f:
                    json.dump([], f)

    @classmethod
    def _save_local(cls, data):
        try:
            history = []
            if os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'r') as f:
                    history = json.load(f)
            history.append(data)
            with open(cls.LOCAL_STORAGE_PATH, 'w') as f:
                json.dump(history, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save to local storage: {e}")

    @classmethod
    def insert_message(cls, session_id, user_message, response):
        msg_doc = {
            "session_id": session_id,
            "message": user_message,
            "response": response,
            "timestamp": datetime.now().isoformat()
        }
        
        if cls.available:
            try:
                cls.db.messages.insert_one(msg_doc)
                logger.info(f"Message inserted for session: {session_id}")
                return
            except Exception as e:
                logger.error(f"Failed to insert into MongoDB: {e}")
        
        # Fallback to local
        cls._save_local(msg_doc)
        logger.info(f"Message saved to LOCAL FALLBACK for session: {session_id}")

    @classmethod
    def get_history(cls, session_id, limit=50):
        if cls.available:
            try:
                cursor = cls.db.messages.find({"session_id": session_id}).sort("_id", 1).limit(limit)
                history = []
                for doc in cursor:
                    doc['_id'] = str(doc['_id'])
                    history.append(doc)
                return history
            except Exception as e:
                logger.error(f"Failed to fetch from MongoDB: {e}")
        
        # Fallback to local
        try:
            if os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'r') as f:
                    history = json.load(f)
                return [m for m in history if m.get("session_id") == session_id][-limit:]
        except Exception as e:
            logger.error(f"Failed to fetch from local storage: {e}")
        return []

    @classmethod
    def get_all_sessions(cls):
        if cls.available:
            try:
                pipeline = [
                    {"$sort": {"_id": 1}},
                    {"$group": {
                        "_id": "$session_id",
                        "first_message": {"$first": "$message"},
                        "timestamp": {"$first": "$_id"}
                    }},
                    {"$sort": {"timestamp": -1}}
                ]
                cursor = cls.db.messages.aggregate(pipeline)
                return [{"session_id": doc["_id"], "title": doc["first_message"]} for doc in cursor]
            except Exception as e:
                logger.error(f"Failed to fetch sessions from MongoDB: {e}")

        # Fallback to local
        try:
            if os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'r') as f:
                    history = json.load(f)
                sessions = {}
                for m in history:
                    sid = m.get("session_id")
                    if sid not in sessions:
                        sessions[sid] = m.get("message")[:30] + "..."
                return [{"session_id": sid, "title": title} for sid, title in sessions.items()]
        except Exception as e:
            logger.error(f"Failed to fetch sessions from local storage: {e}")
        return []

    @classmethod
    def delete_session(cls, session_id):
        if cls.available:
            try:
                cls.db.messages.delete_many({"session_id": session_id})
                return True
            except Exception as e:
                logger.error(f"Failed to delete session from MongoDB: {e}")
        
        # Local cleanup
        try:
            if os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'r') as f:
                    history = json.load(f)
                new_history = [m for m in history if m.get("session_id") != session_id]
                with open(cls.LOCAL_STORAGE_PATH, 'w') as f:
                    json.dump(new_history, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to delete session locally: {e}")
        return False

    @classmethod
    def update_feedback(cls, message_text, session_id, feedback_type):
        if cls.available:
            try:
                last_msg = cls.db.messages.find_one(
                    {"message": message_text, "session_id": session_id},
                    sort=[("_id", -1)]
                )
                if last_msg:
                    cls.db.messages.update_one(
                        {"_id": last_msg["_id"]},
                        {"$set": {"feedback": feedback_type}}
                    )
                    return True
            except Exception as e:
                logger.error(f"Failed to update feedback in MongoDB: {e}")
        
        # Local update
        try:
            if os.path.exists(cls.LOCAL_STORAGE_PATH):
                with open(cls.LOCAL_STORAGE_PATH, 'r') as f:
                    history = json.load(f)
                for m in reversed(history):
                    if m.get("message") == message_text and m.get("session_id") == session_id:
                        m["feedback"] = feedback_type
                        break
                with open(cls.LOCAL_STORAGE_PATH, 'w') as f:
                    json.dump(history, f, indent=2)
                return True
        except Exception as e:
            logger.error(f"Failed to update feedback locally: {e}")
        return False
