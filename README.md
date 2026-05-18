# Axiom AI — World-Class Rule-Based & Hybrid Chatbot

Axiom AI is a professional, industry-grade conversational assistant built with a hybrid architecture. It combines a robust **Rule-Based NLP Engine** with **Fuzzy Matching**, **Multi-language Translation**, and an **LLM Fallback** system (powered by Google Gemini 2.5 Flash).

## 🌟 Key Features

- **Hybrid Intelligence:** Rule-based engine for instant deterministic answers + Gemini 2.5 Flash LLM fallback for complex queries.
- **Fuzzy Intent Matching:** Powered by `thefuzz` (Levenshtein distance) to handle typos and slang.
- **Multilingual Support:** Automatically detects language and translates conversations in real-time (100+ languages).
- **Premium UI/UX:** Glassmorphic, fully responsive design with Light/Dark mode and Framer Motion animations.
- **Voice Interaction:** Speech-to-Text integration using the Web Speech API.
- **RLHF Feedback System:** Thumbs Up/Down feedback on every bot response to log improvement signals.
- **Session Management:** UUID-based session tracking with MongoDB Atlas; graceful local JSON fallback when offline.
- **Chat Export:** One-click export of the full conversation as a `.txt` file (opens automatically in Notepad).
- **Docker Ready:** Deploy the entire full-stack app with a single `docker-compose up` command.
- **Automated Testing:** Full API and NLP test coverage using `pytest`.

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| **Frontend** | Next.js 15, React 19, Tailwind CSS v4, Framer Motion, React Icons |
| **Backend** | Python 3.11, Flask, NLTK, Google Generative AI (Gemini 2.5 Flash) |
| **Database** | MongoDB Atlas (with local JSON fallback) |
| **DevOps** | Docker, Docker Compose, Python Rotating File Logger |

## 🚀 Quick Start (Docker)

Ensure you have [Docker](https://www.docker.com/) installed, then run:

```bash
docker-compose up --build
```

The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:5000

## 🛠️ Manual Installation

### Backend
```bash
cd backend
pip install -r requirements.txt
```
Create a `.env` file based on `.env.example`:
```env
PORT=5000
MONGODB_URI=mongodb+srv://<user>:<pass>@cluster.mongodb.net/
DB_NAME=chatbotDB
GEMINI_API_KEY=your_gemini_api_key
```
```bash
python app.py
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

## 🧪 Running Tests

```bash
cd backend
pytest
```

## 📂 Project Structure

```text
├── docker-compose.yml          # Multi-container orchestration
├── README.md
├── backend/
│   ├── app.py                  # Flask application entry point
│   ├── config.py               # Environment config loader
│   ├── requirements.txt
│   ├── core/
│   │   ├── nlp_engine.py       # Hybrid NLP + Gemini engine
│   │   └── intents.json        # Rule-based intent definitions
│   ├── database/
│   │   └── mongo.py            # MongoDB wrapper + local JSON fallback
│   ├── routes/
│   │   └── chat_routes.py      # Flask REST API endpoints
│   ├── utils/
│   │   └── logger.py           # Rotating file logger
│   ├── tests/                  # Pytest test suite
│   ├── logs/                   # Runtime log files (git-ignored)
│   └── Dockerfile
└── frontend/
    ├── app/
    │   ├── page.js             # Main chatbot UI component
    │   ├── layout.js           # Root layout + metadata
    │   └── globals.css         # Global styles & animations
    └── Dockerfile
```

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/chat` | Send a message, get AI response |
| `GET` | `/history?session_id=...` | Fetch conversation history |
| `GET` | `/sessions` | List all sessions |
| `DELETE` | `/sessions/<id>` | Delete a session |
| `POST` | `/feedback` | Submit thumbs up/down feedback |
| `GET` | `/status` | System health check |

## 🤝 Contributing

Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License

This project is licensed under the MIT License.
