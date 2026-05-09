from pymongo import MongoClient
import sys
import os

# Add the parent directory to the path so we can import config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import Config
from utils.logger import logger

class MongoDB:
    client = None
    db = None
    available = False

    @classmethod
    def connect(cls):
        try:
            cls.client = MongoClient(Config.MONGODB_URI, serverSelectionTimeoutMS=2000)
            cls.db = cls.client[Config.DB_NAME]
            cls.db.command("ping")
            cls.available = True
            logger.info("Successfully connected to MongoDB.")
        except Exception as e:
            logger.error(f"MongoDB connection failed. Chats will not be saved. Error: {e}")
            cls.available = False

    @classmethod
    def insert_message(cls, session_id, user_message, response):
        if cls.available:
            try:
                cls.db.messages.insert_one({
                    "session_id": session_id,
                    "message": user_message,
                    "response": response
                })
                logger.info(f"Message inserted for session: {session_id}")
            except Exception as e:
                logger.error(f"Failed to insert into MongoDB: {e}")

    @classmethod
    def get_history(cls, session_id, limit=50):
        if not cls.available:
            return []
        try:
            # Sort by _id ascending for natural chat flow when loading
            cursor = cls.db.messages.find({"session_id": session_id}).sort("_id", 1).limit(limit)
            history = []
            for doc in cursor:
                doc['_id'] = str(doc['_id'])
                history.append(doc)
            return history
        except Exception as e:
            logger.error(f"Failed to fetch from MongoDB: {e}")
            return []

    @classmethod
    def get_all_sessions(cls):
        """Returns a list of unique sessions with their first user message as a title."""
        if not cls.available:
            return []
        try:
            # Use aggregation to get unique session_ids and their first message
            pipeline = [
                {"$sort": {"_id": 1}},
                {"$group": {
                    "_id": "$session_id",
                    "first_message": {"$first": "$message"},
                    "timestamp": {"$first": "$_id"}
                }},
                {"$sort": {"timestamp": -1}} # Newest chats first
            ]
            cursor = cls.db.messages.aggregate(pipeline)
            return [{"session_id": doc["_id"], "title": doc["first_message"]} for doc in cursor]
        except Exception as e:
            logger.error(f"Failed to fetch sessions: {e}")
            return []

    @classmethod
    def delete_session(cls, session_id):
        if not cls.available:
            return False
        try:
            result = cls.db.messages.delete_many({"session_id": session_id})
            logger.info(f"Deleted session {session_id}. Deleted count: {result.deleted_count}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete session {session_id}: {e}")
            return False

    @classmethod
    def update_feedback(cls, message_text, session_id, feedback_type):
        """
        Update feedback for the most recent message matching the text and session.
        feedback_type: 'up' or 'down'
        """
        if not cls.available:
            return False
        try:
            # Find the most recent message with this text in this session
            last_msg = cls.db.messages.find_one(
                {"message": message_text, "session_id": session_id},
                sort=[("_id", -1)]
            )
            if last_msg:
                cls.db.messages.update_one(
                    {"_id": last_msg["_id"]},
                    {"$set": {"feedback": feedback_type}}
                )
                logger.info(f"Updated feedback to '{feedback_type}' for session {session_id}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to update feedback: {e}")
            return False
