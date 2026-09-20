from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is three levels above backend/app/core/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = _PROJECT_ROOT / "ja_assure.db"


class Settings(BaseSettings):
    # Default is None so the type-checker is satisfied; the fail-fast check
    # below raises loudly at import time when the key is missing.
    GROQ_API_KEY: str | None = None
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    HUNTER_API_KEY: str | None = None

    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()

if not settings.GROQ_API_KEY:
    raise RuntimeError(
        "Missing GROQ_API_KEY. Create backend/.env (see .env.example) and set it."
    )
