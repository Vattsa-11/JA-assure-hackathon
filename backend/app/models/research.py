from sqlalchemy import Column, Integer, String, UniqueConstraint

from app.models.base import BaseModel


class CompetitorDigestEntry(BaseModel):
    __tablename__ = "competitor_digest_entries"

    competitor_url = Column(String, nullable=False, index=True)
    last_snapshot_hash = Column(String, nullable=True)
    suggested_action = Column(String, nullable=True)


class TrackedCompetitor(BaseModel):
    """A competitor on the automated watchlist.

    ``status`` tracks how it entered the list:
      - active:    scraped OK, on the auto-scan rotation
      - major:     seeded known major competitor (same rotation)
      - unreachable: last N scans failed; skipped until it responds again
    """
    __tablename__ = "tracked_competitors"
    __table_args__ = (UniqueConstraint("competitor_url", name="uq_tracked_competitor_url"),)

    competitor_url = Column(String, nullable=False, index=True)
    name = Column(String, nullable=True)
    source = Column(String, nullable=False, default="manual")  # manual | major | ai
    status = Column(String, nullable=False, default="active")  # active | unreachable
    consecutive_failures = Column(Integer, nullable=False, default=0)
