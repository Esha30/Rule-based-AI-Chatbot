# Axiom AI - World-Class Rule-Based & Hybrid Chatbot

Axiom AI is a professional, industry-grade conversational assistant built with a hybrid architecture. It combines a robust **Rule-Based Engine** with **Fuzzy Matching**, **Multi-language Translation**, and an **LLM Fallback** system (powered by Google Gemini).

## 🌟 Key Features

- **Hybrid Intelligence:** Uses a rule-based engine for speed and an LLM (Gemini 1.5 Flash) for complex queries.
- **Fuzzy Intent Matching:** Powered by `thefuzz` (Levenshtein distance) to handle typos and slang.
- **Multilingual Support:** Automatically detects your language and translates conversations in real-time (Supports 100+ languages).
- **Premium UI/UX:** A glassmorphic, responsive design with Light/Dark mode support and Framer Motion animations.
- **Voice Interaction:** Speech-to-Text integration using the Web Speech API.
- **RLHF Feedback System:** Users can provide Thumbs Up/Down feedback to help improve the model.
- **Session Management:** Unique session tracking via UUIDs and MongoDB.
- **Markdown Export:** One-click chat transcript export as `.md` files.
- **Docker Ready:** Deploy the entire stack with a single command.
- **Automated Testing:** Fully tested API and NLP logic using `pytest`.

## 🛠️ Tech Stack

- **Frontend:** Next.js 16+, React 19, Tailwind CSS v4, Framer Motion, Lucide Icons.
- **Backend:** Python 3.11+, Flask, NLTK, Google Generative AI (Gemini), GoogleTrans, LangDetect.
- **Database:** MongoDB.
- **DevOps:** Docker, Docker Compose, Python Logging (Rotating Files).

## 🚀 Quick Start (Docker)

Ensure you have [Docker](https://www.docker.com/) installed, then run:

```bash
docker-compose up --build
```
The app will be available at:
- **Frontend:** http://localhost:3000
- **Backend:** http://localhost:5000

## 🛠️ Manual Installation

### Backend
1. `cd backend`
2. `pip install -r requirements.txt`
3. Create a `.env` file based on `.env.example` (or use the provided `.env`):
   ```env
   PORT=5000
   MONGODB_URI=mongodb://localhost:27017/
   DB_NAME=chatbotDB
   GEMINI_API_KEY=your_gemini_key
   ```
4. `python app.py`

### Frontend
1. `cd frontend`
2. `npm install`
3. `npm run dev`

## 🧪 Running Tests
To verify the application integrity:
```bash
cd backend
pytest
```

## 📂 Project Structure
```text
├── docker-compose.yml        # Multi-container orchestration
├── backend/
│   ├── core/                 # NLP Engine & Intents dataset
│   ├── database/             # MongoDB wrapper
│   ├── routes/               # Flask API endpoints
│   ├── utils/                # Logging & helpers
│   ├── tests/                # Pytest suite
│   ├── logs/                 # System log files
│   └── Dockerfile            # Backend container config
└── frontend/
    ├── app/                  # Next.js Pages & Components
    └── Dockerfile            # Frontend container config
```

## 🤝 Contributing
Contributions are welcome! Feel free to open an issue or submit a pull request.

## 📄 License
This project is licensed under the MIT License.
