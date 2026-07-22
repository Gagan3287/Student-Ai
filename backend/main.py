"""
StudyMate AI — FastAPI application entry point.

Architecture note:
  Every AI call (Groq text generation, Gemini embeddings) is an async HTTPS
  request to an external API. FastAPI's async support means a single-threaded
  process can handle many concurrent in-flight requests while waiting for those
  external responses — important on Render's free tier (0.1 CPU, 512 MB RAM).
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import create_tables
from app.routers import auth, documents, flashcards, quizzes, chat, concepts, dashboard, resume


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Startup / shutdown lifecycle manager.
    - Creates all database tables on first run (idempotent: safe to call repeatedly).
    - Loads the retention model (Phase 6) if the joblib file exists.
    """
    # Create DB tables (runs CREATE TABLE IF NOT EXISTS — safe for re-deploys)
    await create_tables()

    # Phase 6: load retention model at startup so inference is instant per-request
    from app.ml.retention_inference import RetentionPredictor
    RetentionPredictor.load()

    yield  # app is running

    # Shutdown: nothing to clean up (stateless service)


app = FastAPI(
    title="StudyMate AI API",
    description=(
        "AI-powered study and placement companion for engineering students. "
        "Upload notes → get summaries, flashcards, quizzes, RAG chatbot, and "
        "an adaptive spaced-repetition scheduler powered by a self-trained "
        "retention model."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# ─── CORS ─────────────────────────────────────────────────────────────────────
# Allow the Next.js frontend (Vercel) to call the FastAPI backend (Render).
# In production, ALLOWED_ORIGINS should be set to your exact Vercel domain.
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Routers ──────────────────────────────────────────────────────────────────
API_PREFIX = "/api/v1"

app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["auth"])
app.include_router(documents.router, prefix=f"{API_PREFIX}/documents", tags=["documents"])
app.include_router(flashcards.router, prefix=f"{API_PREFIX}/flashcards", tags=["flashcards"])
app.include_router(quizzes.router, prefix=f"{API_PREFIX}/quizzes", tags=["quizzes"])
app.include_router(chat.router, prefix=f"{API_PREFIX}/chat", tags=["chat"])
app.include_router(concepts.router, prefix=f"{API_PREFIX}/concepts", tags=["concepts"])
app.include_router(dashboard.router, prefix=f"{API_PREFIX}/dashboard", tags=["dashboard"])
app.include_router(resume.router, prefix=f"{API_PREFIX}/resume", tags=["resume"])


@app.get("/", tags=["health"])
async def root():
    """Health-check endpoint. Render uses this to confirm the service is up."""
    return {"status": "ok", "service": "StudyMate AI API", "version": "1.0.0"}


@app.get("/health", tags=["health"])
async def health():
    """Explicit health endpoint — useful for uptime monitoring / keep-alive pings."""
    return {"status": "healthy"}
