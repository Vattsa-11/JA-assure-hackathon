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

    # Postiz social publishing (https://postiz.com). When POSTIZ_API_KEY is set,
    # approved campaigns can be published straight from the review modal.
    POSTIZ_API_KEY: str | None = None
    POSTIZ_API_URL: str = "https://api.postiz.com/public/v1"

    # Image generation provider: "pollinations" (free, no key) | "replicate" | "auto"
    # (auto = pollinations first, replicate fallback)
    IMAGE_PROVIDER: str = "auto"
    # Replicate image generation (https://replicate.com/account/api-tokens)
    REPLICATE_API_TOKEN: str | None = None
    REPLICATE_IMAGE_MODEL: str = "tencent/hunyuan-image-2.1"
    # Text-to-video model slot (default: HunyuanVideo on Replicate).
    # HunyuanVideo-1.5 is Hugging Face weights-only today; point this at any
    # hosted 1.5 endpoint (Replicate/fal/custom) to switch — no code change.
    REPLICATE_VIDEO_MODEL: str = "tencent/hunyuan-video"

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
        unique = []
        for raw in keys:
            k = raw.strip()
            if k and k not in seen:
                seen.add(k)
                unique.append(k)
        return unique

settings = Settings()

# Fail fast (same as a required field would) if the API key is missing.
if not settings.GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not set. Configure it in backend/.env or the environment.")
