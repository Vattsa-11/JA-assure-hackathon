from sqlalchemy import Column, String
from app.models.base import BaseModel

class CompetitorDigestEntry(BaseModel):
    __tablename__ = "competitor_digest_entries"

    competitor_url = Column(String, nullable=False, index=True)
    last_snapshot_hash = Column(String, nullable=True)
    suggested_action = Column(String, nullable=True)
