# Better Word For

AI-powered word suggestions that understand context, emotion, and tone — not just synonyms.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)

---

## Overview

Standard thesauruses return a flat list of synonyms. Better Word For works differently — you describe what you're trying to say (a word, a phrase, a feeling), and the AI returns suggestions with definitions, usage examples, tone labels, and emotion tags. It's built around the idea that finding the right word is rarely about picking a synonym; it's about matching precision to intent.

The app supports two main modes: **word search** (find alternatives for any input) and **sentence rewrite** (paste text, specify a goal, get a rewritten version with change-by-change explanations).

---

## How the AI Works

Every search runs a three-step prompt chain, where each step's output feeds directly into the next:

**Step 1 — Emotion Analysis**
The model reads the input and extracts the primary emotion, secondary emotion, intensity, and a short context summary.

**Step 2 — Word Generation**
Using the emotion analysis as context, the model generates a best-fit word and a set of ranked alternatives.

**Step 3 — Explanation & Categorization**
Each word gets an explanation of why it fits, plus categorical labels (register, tone, origin, rarity).

The three-step chain produces meaningfully better results than a single prompt because each model call has a narrower, cleaner task.

### Parallel Model Racing

Requests are fired simultaneously to nine free models via OpenRouter. Whichever responds first wins; the rest are cancelled. This keeps latency low on free-tier models and provides automatic failover if one is rate-limited or down.

| Model | Provider |
|---|---|
| Trinity Large Preview | Arcee AI |
| Trinity Mini | Arcee AI |
| Gemma 3 12B | Google |
| Gemma 3 4B | Google |
| Gemma 3n E4B | Google |
| Nemotron 3 Nano 30B | NVIDIA |
| Nemotron Nano 9B v2 | NVIDIA |
| Step 3.5 Flash | StepFun |
| GLM 4.5 Air | Z-AI |

---

## Features

- Word suggestions with definitions, example sentences, tone register, origin, emotion tags, and rarity scores
- Sentence rewrite mode with word-by-word change explanations
- Word of the Day — AI-curated daily vocabulary, cached and served from the database
- Vocabulary Bank — save words with custom notes and tags
- Search history — paginated, with full result recall
- Like/dislike feedback on individual suggestions

---

## Architecture

```
frontend/                        # React 18 + TypeScript + Vite
backend/
├── app/
│   ├── api/routes.py            # All endpoints
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   └── database.py          # Async SQLAlchemy + NeonDB
│   ├── models/
│   │   ├── models.py            # ORM models
│   │   └── schemas.py           # Request/response schemas
│   ├── services/
│   │   └── ai_service.py        # Prompt chain + parallel model racing
│   └── main.py
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Run the 3-step AI pipeline for word suggestions |
| `POST` | `/api/rewrite` | Rewrite a sentence toward a specified goal |
| `GET` | `/api/word-of-the-day` | Cached daily word |
| `POST` | `/api/saved-words` | Save a word to the vocabulary bank |
| `GET` | `/api/saved-words` | List saved words |
| `DELETE` | `/api/saved-words/{id}` | Remove a saved word |
| `POST` | `/api/feedback` | Submit feedback on a suggestion |
| `GET` | `/api/history` | Paginated search history |
| `GET` | `/health` | Health check |

### Database

PostgreSQL (NeonDB free tier). Schema:

```
users
searches → word_results
saved_words
feedback
word_of_the_day   (cached, updated daily via cron)
```

---

## Getting Started

**Prerequisites:** Python 3.11+, Node.js 18+, a [NeonDB](https://neon.tech) database, and an [OpenRouter](https://openrouter.ai) API key (both have free tiers).

### Backend

```bash
cd backend
python -m venv venv
source venv/bin/activate      # Windows: .\venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Fill in DATABASE_URL and OPENROUTER_API_KEY

uvicorn app.main:app --reload --port 8000
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173).

---

## Deployment

**Frontend → Vercel**
Set the root directory to `frontend` and add `VITE_API_URL` pointing to your backend.

**Backend → Railway or Render**
Set the root directory to `backend`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`.

**Database → NeonDB**
Copy the connection string and replace `postgresql://` with `postgresql+asyncpg://`. Remove `sslmode=require` from the query string and add `ssl=require` instead.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (asyncpg format) |
| `OPENROUTER_API_KEY` | Yes | From openrouter.ai |
| `FRONTEND_URL` | No | CORS origin (default: localhost:5173) |
| `DEBUG` | No | Enable debug mode (default: false) |
| `RATE_LIMIT_PER_MINUTE` | No | Default: 30 |
| `RATE_LIMIT_PER_DAY` | No | Default: 500 |

---

## Tech Stack

| | |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router |
| Styling | Vanilla CSS — dark theme, glassmorphism |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| Database | PostgreSQL via NeonDB, SQLAlchemy (async) |
| AI | OpenRouter — parallel model racing |
| Icons | Lucide React |

---

## License

MIT