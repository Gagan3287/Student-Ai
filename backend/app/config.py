"""
Application configuration — all settings loaded from environment variables.

pydantic-settings reads values from the environment (and from a .env file when
ENVIRONMENT=development). Every field is typed and validated at startup, so a
missing required variable causes an immediate, descriptive error rather than a
mysterious failure mid-request.
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # ── JWT ───────────────────────────────────────────────────────────────────
    jwt_secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expiry_hours: int = 24

    # ── Groq (primary text-generation adapter) ────────────────────────────────
    groq_api_key: str
    groq_model_primary: str = "llama-3.3-70b-versatile"
    groq_model_fallback: str = "llama-3.1-8b-instant"

    # ── Gemini (embeddings-only adapter) ──────────────────────────────────────
    gemini_api_key: str
    gemini_embedding_model: str = "gemini-embedding-001"
    gemini_embedding_dimensions: int = 768

    # ── Supabase Storage ──────────────────────────────────────────────────────
    supabase_url: str
    supabase_service_key: str
    supabase_bucket: str = "studymate-uploads"

    # ── App ───────────────────────────────────────────────────────────────────
    environment: str = "development"
    allowed_origins: str = "http://localhost:3000"

    @property
    def allowed_origins_list(self) -> list[str]:
        """Parse comma-separated ALLOWED_ORIGINS env var into a list."""
        return [origin.strip() for origin in self.allowed_origins.split(",")]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,  # DATABASE_URL and database_url are both accepted
    )


# Module-level singleton — import this object everywhere instead of re-reading env
settings = Settings()
