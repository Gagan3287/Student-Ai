<div align="center">

# 🎓 StudyMate AI

### Your AI-powered study and placement companion for engineering students

[![Live Demo](https://img.shields.io/badge/demo-live-success?style=for-the-badge&logo=vercel)](https://studymate-aix.vercel.app/)
[![Frontend](https://img.shields.io/badge/frontend-Next.js%2014-black?style=for-the-badge&logo=next.js)](https://nextjs.org/)
[![Backend](https://img.shields.io/badge/backend-FastAPI-009688?style=for-the-badge&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Database](https://img.shields.io/badge/database-Supabase%20%2B%20pgvector-3ECF8E?style=for-the-badge&logo=supabase)](https://supabase.com/)

**[🚀 Try it live → studymate-aix.vercel.app](https://studymate-aix.vercel.app/)**

</div>

---

## 📖 What is StudyMate AI?

StudyMate AI turns raw class notes and PDFs into a full study system. Upload your material once, and it gives you:

| Feature | What it does |
|---|---|
| 📝 **Auto-Summaries** | Condenses dense lecture notes/PDFs into structured summaries |
| 🧠 **Adaptive Flashcards** | Spaced-repetition flashcards that adjust to how well you know each concept |
| 💬 **RAG Chatbot** | Ask questions and get answers grounded *only* in your own uploaded material — no hallucinated syllabus content |
| 🕸️ **Concept Knowledge Graph** | Visualizes how concepts in your notes connect to each other |
| 📄 **Resume vs JD Skill-Gap Analyzer** | Compares your resume against a job description and highlights exactly what skills you're missing |

Built for engineering students juggling exams *and* placements — one tool for both.

---

## 🏗️ Architecture Overview

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

**Why this stack?**
- **Next.js 14 (App Router)** — fast, SEO-friendly, server components for the dashboard UI
- **FastAPI** — async Python backend, auto-generated OpenAPI docs, great for RAG pipelines
- **Supabase (Postgres + pgvector)** — one database for relational data *and* vector similarity search, no separate vector DB needed
- **Groq** — extremely fast LLM inference for chatbot responses and summarization
- **Gemini** — used specifically for embeddings (cost-effective, high quality)

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for the full technical write-up, including the Phase 6 self-trained retention model used for adaptive flashcard scheduling.

---

## ✨ Live Demo

🔗 **[studymate-aix.vercel.app](https://studymate-aix.vercel.app/)**

> ⚠️ The backend runs on Render's free tier, which sleeps after 15 minutes of inactivity. The first request after idle time may take 30–60 seconds to wake up — subsequent requests are fast.

---

## 🛠️ Tech Stack

**Frontend:** Next.js 14, App Router, TypeScript, Tailwind CSS
**Backend:** FastAPI, Python 3.11+
**Database:** Supabase (Postgres) + pgvector for embeddings
**Storage:** Supabase Storage (private buckets for uploaded PDFs)
**LLM:** Groq API (text generation)
**Embeddings:** Google Gemini API
**Hosting:** Vercel (frontend) · Render (backend)

---

## 🚀 Getting Started Locally

### Prerequisites

- **Node.js** 18+ and npm
- **Python** 3.11+
- **Git**
- A free **Supabase** account → [supabase.com](https://supabase.com)
- A free **Groq** API key → [console.groq.com](https://console.groq.com)
- A free **Gemini** API key → [aistudio.google.com](https://aistudio.google.com) *(embeddings only)*

### 1. Clone the repo

```bash
git clone https://github.com/your-username/studymate-ai.git
cd studymate-ai
```

### 2. Get your API keys

<details>
<summary><strong>Google Gemini API Key (embeddings)</strong></summary>

1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Sign in with your Google account (free, no credit card needed)
3. Click **Get API key** → **Create API key**
4. Copy the key — set it as `GEMINI_API_KEY` in `backend/.env`

</details>

<details>
<summary><strong>Groq API Key (LLM text generation)</strong></summary>

1. Go to [console.groq.com](https://console.groq.com)
2. Sign up for a free account
3. Navigate to **API Keys** → **Create API Key**
4. Copy the key — set it as `GROQ_API_KEY` in `backend/.env`

</details>

<details>
<summary><strong>Supabase (Postgres + file storage)</strong></summary>

1. Go to [supabase.com](https://supabase.com) → **Start your project** (free)
2. Create a new project (choose any region close to you)
3. Wait ~2 minutes for provisioning
4. Go to **Project Settings → Database → Connection String** (URI format) → copy for `DATABASE_URL`
5. Go to **Project Settings → API** → copy `Project URL` for `SUPABASE_URL` and the `service_role` key for `SUPABASE_SERVICE_KEY`
6. Go to **Storage → New bucket** → name it `studymate-uploads` → set to **Private**
7. Run the pgvector extension in the **SQL Editor**:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```

</details>

### 3. Backend setup

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
# Edit .env with your actual API keys (see step 2 above)

# Start the dev server
uvicorn main:app --reload --port 8000
```

- API: `http://localhost:8000`
- Interactive docs: `http://localhost:8000/docs`

### 4. Frontend setup

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

- App: `http://localhost:3000`

---

## 🔐 Environment Variables

See `backend/.env.example` and `frontend/.env.example` for the full list of required variables.

> **Never commit real API keys to Git.** `.gitignore` excludes all `.env` files by default.

---

## ☁️ Deployment

### Backend → Render (Free Web Service)

1. Push your repo to GitHub
2. Go to [render.com](https://render.com) → **New → Web Service**
3. Connect your GitHub repo
4. Configure:
   | Setting | Value |
   |---|---|
   | Root directory | `backend` |
   | Runtime | Python 3 |
   | Build command | `pip install -r requirements.txt` |
   | Start command | `uvicorn main:app --host 0.0.0.0 --port $PORT` |
   | Instance type | Free |
5. Add all environment variables from `backend/.env.example`
6. Click **Create Web Service**

> Render's free tier sleeps after 15 minutes idle (cold start ~30–60s). For live demos, ping the URL a minute beforehand. For production, upgrade to a paid instance or add a keep-alive cron ping.

### Frontend → Vercel

1. Go to [vercel.com](https://vercel.com) → **New Project**
2. Import your GitHub repo
3. Set **Root Directory** to `frontend`
4. Add environment variable: `NEXT_PUBLIC_API_URL` = your Render backend URL
5. Click **Deploy**

---

## 📊 Project Report / Viva Notes

See [`ARCHITECTURE.md`](./ARCHITECTURE.md) for a full breakdown of every technology decision and the Phase 6 self-trained retention model — the reference document for answering evaluator questions on design choices.

---

<div align="center">

**[🔗 Live App](https://studymate-aix.vercel.app/)** · Built for students, by a student

</div>
