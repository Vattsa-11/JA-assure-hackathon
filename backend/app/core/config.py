from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is two levels above backend/app/core/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = _PROJECT_ROOT / "ja_assure.db"

class Settings(BaseSettings):
    GROQ_API_KEY: str
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    HUNTER_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

settings = Settings()
