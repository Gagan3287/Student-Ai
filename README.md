# StudyMate AI

An AI-powered study and placement companion for engineering students. Upload your class notes/PDFs and get auto-summaries, flashcards with adaptive spaced-repetition, a RAG chatbot scoped to your own material, an interactive concept knowledge graph, and a Resume vs Job Description Skill-Gap Analyzer.

---

## Architecture Overview

```
studymate-ai/
├── backend/        FastAPI (Python) — deployed on Render free tier
├── frontend/       Next.js 14 App Router — deployed on Vercel
├── README.md
└── ARCHITECTURE.md
```

```
Browser ──── HTTPS ──── Vercel (Next.js)
                              │
                         REST calls
                              │
                        Render (FastAPI) ──── Supabase Postgres + pgvector
                              │                       │
                         Groq API              Supabase Storage
                      (text generation)        (uploaded PDFs)
                              │
                         Gemini API
                       (embeddings only)
```

---

## Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**
- A free **Supabase** account → [supabase.com](https://supabase.com)
- A free **Groq** API key → [console.groq.com](https://console.groq.com)
- A free **Gemini** API key → [aistudio.google.com](https://aistudio.google.com) *(embeddings only)*

---

## Getting API Keys

### 1. Google Gemini API Key (for embeddings)
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account (free, no credit card needed)
3. Click **Get API key** → **Create API key**
4. Copy the key — set it as `GEMINI_API_KEY` in `backend/.env`

### 2. Groq API Key (for text generation — LLM)
1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key — set it as `GROQ_API_KEY` in `backend/.env`

### 3. Supabase (Postgres + file storage)
1. Go to [supabase.com](https://supabase.com) → **Start your project** (free)
2. Create a new project (choose any region close to you)
3. Wait ~2 minutes for provisioning
4. Go to **Project Settings → Database → Connection String** (URI format) → copy for `DATABASE_URL`
5. Go to **Project Settings → API** → copy `Project URL` for `SUPABASE_URL` and the `service_role` key for `SUPABASE_SERVICE_KEY`
6. Go to **Storage → New bucket** → name it `studymate-uploads` → set to **Private**
7. Run the pgvector extension: go to **SQL Editor** and run:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

---

## Local Development Setup

### 1. Clone the repo
```bash
git clone https://github.com/your-username/studymate-ai.git
cd studymate-ai
```

### 2. Backend setup
```bash
cd backend

# Create and activate a virtual environment
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your actual API keys (see "Getting API Keys" above)

# Start the dev server
uvicorn main:app --reload --port 8000
```

Backend API will be available at `http://localhost:8000`
Interactive docs at `http://localhost:8000/docs`

### 3. Frontend setup
```bash
cd frontend

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local — set NEXT_PUBLIC_API_URL=http://localhost:8000

# Start the dev server
npm run dev
```

Frontend will be available at `http://localhost:3000`

---

## Environment Variables

See `backend/.env.example` and `frontend/.env.example` for all required variables.

**Never commit real API keys to Git.** The `.gitignore` excludes all `.env` files.

---

## Deployment

### Backend → Render (free Web Service)

1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Set configuration:
   - **Root directory:** `backend`
   - **Runtime:** Python 3
   - **Build command:** `pip install -r requirements.txt`
   - **Start command:** `uvicorn main:app --host 0.0.0.0 --port $PORT`
   - **Instance type:** Free
5. Add all environment variables from `backend/.env.example` under **Environment → Add Environment Variable**
6. Click **Create Web Service**

> **Note:** Render's free tier sleeps after 15 minutes of inactivity (cold start ~30–60 s).
> For demos, hit the URL one minute before presenting. For production, upgrade to a paid instance
> or add a cron keep-alive ping.

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL
5. Click **Deploy**

---

## Project Report / Viva Notes

See `ARCHITECTURE.md` for a detailed explanation of every technology choice and the Phase 6 self-trained retention model — this is the document to reference when answering evaluator questions about design decisions.
