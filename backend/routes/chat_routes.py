from flask import Blueprint, request, jsonify
import sys
import os
import uuid

# Add parent directory
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from core.nlp_engine import NLPEngine
from database.mongo import MongoDB
from utils.logger import logger

chat_bp = Blueprint('chat', __name__)
nlp_engine = NLPEngine()

@chat_bp.route("/status", methods=["GET"])
def system_status():
    return jsonify({
        "status": "online",
        "database": "connected" if MongoDB.available else "local_fallback",
        "engine": "Axiom NLP v4.2",
        "patterns_loaded": len(nlp_engine.knowledge_base)
    }), 200

@chat_bp.route("/chat", methods=["POST"])
def chat():
    data = request.json
    if not data or "message" not in data:
        logger.warning("Received invalid chat request without message payload.")
        return jsonify({"error": "Invalid request. 'message' field is required."}), 400

    user_message = data["message"]
    # Get session ID from client or generate a new one
    session_id = data.get("session_id", str(uuid.uuid4()))
    
    try:
        result = nlp_engine.get_response(user_message)
        response_text = result["text"]
        source = result["source"]
        
        # Store Chats in MongoDB
        MongoDB.insert_message(session_id, user_message, response_text)
        
        return jsonify({
            "response": response_text,
            "session_id": session_id,
            "source": source
        }), 200
    except Exception as e:
        logger.error(f"Error processing chat: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@chat_bp.route("/history", methods=["GET"])
def history():
    session_id = request.args.get("session_id")
    if not session_id:
        return jsonify({"error": "session_id parameter is required."}), 400
        
    try:
        chats = MongoDB.get_history(session_id)
        return jsonify(chats), 200
    except Exception as e:
        logger.error(f"Error fetching history: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@chat_bp.route("/sessions", methods=["GET"])
def get_sessions():
    try:
        sessions = MongoDB.get_all_sessions()
        return jsonify(sessions), 200
    except Exception as e:
        logger.error(f"Error fetching sessions: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@chat_bp.route("/sessions/<session_id>", methods=["DELETE"])
def delete_session(session_id):
    try:
        success = MongoDB.delete_session(session_id)
        if success:
            return jsonify({"status": "success"}), 200
        return jsonify({"error": "Session not found."}), 404
    except Exception as e:
        logger.error(f"Error deleting session: {e}")
        return jsonify({"error": "An internal error occurred."}), 500

@chat_bp.route("/feedback", methods=["POST"])
def feedback():
    data = request.json
    if not data or "message" not in data or "feedback" not in data or "session_id" not in data:
        return jsonify({"error": "Invalid payload."}), 400
        
    success = MongoDB.update_feedback(data["message"], data["session_id"], data["feedback"])
    if success:
        return jsonify({"status": "success"}), 200
    return jsonify({"error": "Message not found."}), 404
