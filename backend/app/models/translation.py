from sqlalchemy import Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class TranslationCache(BaseModel):
    """Stores one row per (source text, target language) pair.

    Keeps the app's dynamic content (drafts, outreach emails, fit reasons,
    topics) translatable on demand without ever calling the LLM twice for
    the same string/language combination.
    """
    __tablename__ = "translation_cache"
    __table_args__ = (
        UniqueConstraint("source_hash", "target_language", name="uq_translation_hash_lang"),
    )

    source_hash: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    target_language: Mapped[str] = mapped_column(String(8), index=True, nullable=False)
    source_text: Mapped[str] = mapped_column(String, nullable=False)
    translated_text: Mapped[str] = mapped_column(String, nullable=False)
    # Number of times a request reused this cached row (observability)
    hit_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
