# Lexify — Better Word For

AI-powered word suggestions that understand context, emotion, and tone — not just synonyms.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.11+-green.svg)
![React](https://img.shields.io/badge/react-18+-61DAFB.svg)
![FastAPI](https://img.shields.io/badge/fastapi-0.115+-009688.svg)

---

## Overview

Standard thesauruses return a flat list of synonyms. Lexify works differently — you describe what you're trying to say (a word, a phrase, a feeling), and the AI returns suggestions with definitions, usage examples, tone labels, and emotion tags. It's built around the idea that finding the right word is rarely about picking a synonym; it's about matching precision to intent.

The app supports two main modes: **word search** (find alternatives for any input) and **sentence rewrite** (paste text, specify a goal, get a rewritten version with change-by-change explanations).

---

## How the AI Works

Every search sends a single, structured prompt that asks the model to return emotion analysis, word suggestions, and explanations in one JSON response. The prompt is compressed to ~100 tokens of instructions to minimize latency.

The response includes:
- **Emotion analysis** — primary/secondary emotion, intensity, context summary
- **Best-fit word** — the single best match with a reason
- **5–8 ranked alternatives** — each with strength rating, categories, and an explanation

### Parallel Model Racing

Instead of calling one model and hoping it's fast, Lexify fires the same request to **9 models simultaneously** via OpenRouter. The first successful response wins; the rest are cancelled immediately.

| Model | Provider |
|---|---|
| Gemma 3 4B | Google |
| Gemma 3n E4B | Google |
| Trinity Mini | Arcee AI |
| Nemotron Nano 9B v2 | NVIDIA |
| Step 3.5 Flash | StepFun |
| GLM 4.5 Air | Z-AI |
| Trinity Large Preview | Arcee AI |
| Gemma 3 12B | Google |
| Nemotron 3 Nano 30B | NVIDIA |

Models are ordered fastest-first. Timeout is 20 seconds — if a model hasn't responded by then, it's dropped from the race.

---

## Performance Optimizations

| Optimization | What it does |
|---|---|
| **Single-call pipeline** | Emotion analysis + word generation + explanations in one LLM call instead of three sequential calls. Cuts latency by ~3x. |
| **Parallel model racing** | 9 models called simultaneously. First response wins, rest are cancelled. |
| **Persistent HTTP client** | One shared `httpx.AsyncClient` reused across all requests. Avoids TCP/TLS handshake overhead (~200-500ms saved per request). |
| **In-memory TTL cache** | Identical queries within 1 hour return instantly from cache. LRU eviction at 200 entries. |
| **Compressed prompts** | ~100 input tokens instead of ~180. Less tokenization time, faster model processing. |
| **Reduced max_tokens** | Capped at 1,800 instead of 3,000. Models stop generating sooner since actual responses are ~700 tokens. |
| **Keep-alive self-ping** | Background task pings `/health` every 13 minutes to prevent Render free-tier cold starts. |

Typical response times:
- Cache hit: **instant** (~0ms)
- Warm server: **2–4 seconds**
- Cold start (first request after deploy): **~10 seconds** (mitigated by self-ping + external cron)

---

## Safety & Abuse Protection

### Content Filter

All user input passes through a regex-based content filter before reaching the AI. Blocked inputs return a `400` with a clean error message and never consume AI credits.

The filter covers:
- **English profanity** — fuck, shit, bitch, asshole, and variants (using `\w*` to catch conjugations like "fucking", "shitty")
- **Slurs & hate speech** — racial, ethnic, homophobic slurs
- **Sexual / NSFW content** — pornography, explicit sexual terms
- **Violent threats** — "kill yourself", bomb threats, school shooting references
- **Hindi / Hinglish abuses** — romanized (chutiya, madarchod, bhosdi, gaand, randi, etc.) and Devanagari script (चूतिया, मादरचोद, भोसड़ीके, etc.)

All patterns use word-boundary matching (`\b`) to minimize false positives — "classic" won't trigger on "ass", "assume" won't trigger on "ass".

### Rate Limiting

In-memory sliding window rate limiter applied to AI-heavy endpoints only:

| Limit | Scope |
|---|---|
| **10 requests/minute** | Per IP address |
| **200 requests/day** | Per IP address |

Non-AI endpoints (health checks, saved words, static assets) are not rate-limited. The rate limiter reads `X-Forwarded-For` and `X-Real-IP` headers for accurate IP detection behind Render/Vercel proxies.

### Error Handling

- All error responses include CORS headers so the browser shows the actual error message instead of a generic CORS failure
- Backend errors are caught by a global exception handler that returns "Something went wrong. Please try again." — raw stack traces never leak to the frontend
- DB write failures on search/feedback are non-blocking — the AI response still returns even if the database is down
- Frontend translates status codes into user-friendly messages (429 → "Too many requests", 503 → "AI unavailable", etc.)

---

## Features

- Word suggestions with emotion analysis, tone labels, strength ratings, and explanations
- Sentence rewrite mode with word-by-word change explanations
- Word of the Day — AI-curated daily vocabulary, cached in the database
- Vocabulary Bank — save words with custom notes and tags
- Search history — stored locally in the browser (private per device)
- Like/dislike feedback on individual suggestions
- Dark/light theme toggle with localStorage persistence
- Vercel Analytics integration

---

## Architecture

```
frontend/                        # React 18 + TypeScript + Vite
├── src/
│   ├── components/              # Navbar, Footer, SearchResults, etc.
│   ├── pages/                   # HomePage, HistoryPage, VocabularyPage
│   ├── services/
│   │   ├── api.ts               # Typed API client with error translation
│   │   └── history.ts           # localStorage history manager
│   └── hooks/useTheme.ts        # Dark/light theme hook

backend/
├── app/
│   ├── api/routes.py            # All endpoints
│   ├── core/
│   │   ├── config.py            # Pydantic settings
│   │   ├── database.py          # Async SQLAlchemy + NeonDB
│   │   ├── rate_limiter.py      # Sliding window rate limiter
│   │   └── content_filter.py    # NSFW/abuse regex filter
│   ├── models/
│   │   ├── models.py            # ORM models
│   │   └── schemas.py           # Request/response schemas
│   ├── services/
│   │   └── ai_service.py        # Single-call pipeline + model racing + cache
│   └── main.py                  # FastAPI app, CORS, keep-alive
```

### API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/search` | Content filter → AI pipeline → word suggestions |
| `POST` | `/api/rewrite` | Content filter → AI rewrite with change explanations |
| `GET` | `/api/word-of-the-day` | Cached daily word (DB → AI fallback) |
| `POST` | `/api/saved-words` | Save a word to the vocabulary bank |
| `GET` | `/api/saved-words` | List saved words |
| `DELETE` | `/api/saved-words/{id}` | Remove a saved word |
| `POST` | `/api/feedback` | Submit feedback on a suggestion |
| `GET` | `/health` | Health check (used by keep-alive + external cron) |

### Database

PostgreSQL (NeonDB free tier). Schema:

```
searches → word_results
saved_words
feedback
word_of_the_day   (cached daily)
```

---

## Getting Started

**Prerequisites:** Python 3.11+, Node.js 18+, a [NeonDB](https://neon.tech) database, and an [OpenRouter](https://openrouter.ai) API key (both have free tiers).

### Backend

1. **Navigate to the backend directory:**

   ```bash
   cd backend
   ```

2. **Create and activate a virtual environment:**

   ```bash
   python -m venv venv
   ```

   - **Windows (PowerShell):**
     ```powershell
     .\venv\Scripts\Activate.ps1
     ```
   - **Windows (CMD):**
     ```cmd
     .\venv\Scripts\activate.bat
     ```
   - **macOS / Linux:**
     ```bash
     source venv/bin/activate
     ```

3. **Install dependencies:**

   ```bash
   pip install -r requirements.txt
   ```

   This installs: FastAPI, Uvicorn, SQLAlchemy (async), asyncpg, httpx, Pydantic, python-dotenv, and Alembic.

4. **Set up environment variables:**

   ```bash
   cp .env.example .env
   ```

   > On Windows CMD, use `copy .env.example .env` instead.

   Open `.env` and fill in the required values:

   ```env
   # Required — NeonDB PostgreSQL connection string
   # Use postgresql+asyncpg:// prefix and ?ssl=require (NOT sslmode=require)
   DATABASE_URL=postgresql+asyncpg://user:password@your-host.neon.tech/dbname?ssl=require

   # Required — Get your free API key from https://openrouter.ai/keys
   OPENROUTER_API_KEY=sk-or-v1-your-key-here

   # Optional
   DEBUG=false
   FRONTEND_URL=http://localhost:5173
   RATE_LIMIT_PER_MINUTE=30
   RATE_LIMIT_PER_DAY=500
   ```

5. **Start the development server:**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

   The server will:
   - Auto-create all database tables on first startup (no migrations needed)
   - Start listening at [http://localhost:8000](http://localhost:8000)
   - Show interactive API docs at [http://localhost:8000/docs](http://localhost:8000/docs)

6. **Verify it's running:**

   ```bash
   curl http://localhost:8000/health
   # Expected: {"status":"healthy"}
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

**Backend → Render**
Set the root directory to `backend`. Start command: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`. Add `RENDER_EXTERNAL_URL` for the keep-alive self-ping.

**Database → NeonDB**
Copy the connection string and replace `postgresql://` with `postgresql+asyncpg://`. Replace `sslmode=require` with `ssl=require`.

**Cold start prevention**
Set up an external cron (e.g., cron-job.org) to ping your `/health` endpoint every 10–14 minutes. The backend also self-pings every 13 minutes while running.

---

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DATABASE_URL` | Yes | PostgreSQL connection string (asyncpg format) |
| `OPENROUTER_API_KEY` | Yes | From openrouter.ai |
| `RENDER_EXTERNAL_URL` | No | Backend URL for self-ping keep-alive |
| `FRONTEND_URL` | No | CORS origin (default: localhost:5173) |
| `DEBUG` | No | Enable debug mode (default: false) |

---

## Tech Stack

| | |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router |
| Styling | Vanilla CSS — dark/light theme, glassmorphism |
| Backend | FastAPI, Python 3.11+, Uvicorn |
| Database | PostgreSQL via NeonDB, SQLAlchemy (async) |
| AI | OpenRouter — 9-model parallel racing |
| Analytics | Vercel Analytics |
| Icons | Lucide React |

---

## License

MIT
