from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class CompetitorDigestEntry(BaseModel):
    __tablename__ = "competitor_digest_entries"

    competitor_url: Mapped[str] = mapped_column(String, nullable=False, index=True)
    last_snapshot_hash: Mapped[str | None] = mapped_column(String, nullable=True)
    suggested_action: Mapped[str | None] = mapped_column(String, nullable=True)
