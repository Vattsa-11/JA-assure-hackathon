from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root is two levels above backend/app/core/config.py
_PROJECT_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_DB_PATH = _PROJECT_ROOT / "ja_assure.db"

class Settings(BaseSettings):
    GROQ_API_KEY: str = ""
    # Optional extra keys, comma-separated, for rate-limit load balancing.
    # Effective per-minute token budget = number of keys x provider limit.
    GROQ_API_KEYS: str = ""
    DATABASE_URL: str = f"sqlite:///{_DEFAULT_DB_PATH}"
    HUNTER_API_KEY: str | None = None

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    @property
    def groq_api_key_list(self) -> list[str]:
        """All configured Groq keys, deduplicated.

        Accepts comma-separated lists in either variable, so both of these work:
          GROQ_API_KEY=gsk_a,gsk_b,gsk_c
          GROQ_API_KEYS=gsk_d,gsk_e
        """
        keys = [*self.GROQ_API_KEY.split(","), *self.GROQ_API_KEYS.split(",")]
        seen: set[str] = set()
        unique = [k.strip() for k in keys if k.strip() and not (k.strip() in seen or seen.add(k.strip()))]
        return unique

settings = Settings()

# Fail fast (same as a required field would) if the API key is missing.
if not settings.GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Configure it in backend/.env or the environment.")
