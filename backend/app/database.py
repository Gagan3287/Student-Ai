"""
Database engine, session factory, and base declarative class.

SQLAlchemy 2.x async is available but would require asyncpg driver and more
complex session management. For clarity and Render compatibility we use the
synchronous psycopg2 driver inside a thread pool (FastAPI's run_in_executor
pattern). This is the pragmatic choice for a project of this scale.

pgvector: the `pgvector` package registers a custom SQLAlchemy type (Vector)
and a psycopg2 codec so that VECTOR(768) columns are read/written as Python
lists of floats transparently.
"""

import logging
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

logger = logging.getLogger(__name__)

# ─── Engine ───────────────────────────────────────────────────────────────────
engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,      # verify connections before use (handles Supabase timeouts)
    pool_size=5,             # keep at most 5 idle connections — fits the free tier
    max_overflow=10,         # allow up to 10 extra connections under load
    echo=settings.environment == "development",  # log SQL in dev, not prod
)

# ─── Session factory ──────────────────────────────────────────────────────────
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# ─── Base declarative class ───────────────────────────────────────────────────
class Base(DeclarativeBase):
    pass


# ─── FastAPI dependency ───────────────────────────────────────────────────────
def get_db():
    """
    Yield a database session and ensure it is closed after the request.

    Usage in a route:
        from fastapi import Depends
        from app.database import get_db
        from sqlalchemy.orm import Session

        @router.get("/example")
        def example(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ─── Table creation ───────────────────────────────────────────────────────────
async def create_tables():
    """
    Create all tables defined in the SQLAlchemy models (CREATE TABLE IF NOT EXISTS).

    Called once at FastAPI startup (lifespan). Safe to call on every deploy.

    Note: for production-grade schema migrations (adding columns, renaming, etc.)
    you would use Alembic. For this project, dropping and recreating tables during
    development is acceptable, and adding Alembic is left as an exercise.
    """
    # Import all models so SQLAlchemy knows about them before create_all()
    from app.models import user, document, chunk, flashcard, quiz, chat, concept  # noqa: F401

    try:
        with engine.connect() as conn:
            # Ensure the pgvector extension exists — must run before any table
            # with a VECTOR column is created. Supabase usually has it available
            # but it still needs to be activated per-database.
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            conn.commit()

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created / verified successfully.")
    except Exception as exc:
        logger.error(f"Failed to create database tables: {exc}")
        raise
