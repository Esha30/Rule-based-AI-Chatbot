from flask import Flask
from flask_cors import CORS
from database.mongo import MongoDB
from routes.chat_routes import chat_bp
from config import Config
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_app():
    app = Flask(__name__)
    
    # Configure CORS - allow specific origins in production
    CORS(app)

    # Initialize MongoDB connection
    MongoDB.connect()

    # Register Blueprints
    app.register_blueprint(chat_bp)

    @app.route("/health", methods=["GET"])
    def health_check():
        return {"status": "healthy", "db_connected": MongoDB.available}, 200

    return app

app = create_app()

if __name__ == "__main__":
    app.run(debug=Config.DEBUG, port=Config.PORT)
