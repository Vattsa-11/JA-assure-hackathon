import enum
from sqlalchemy import Column, Integer, String, Enum
from app.models.base import BaseModel

class LeadStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"

class Lead(BaseModel):
    __tablename__ = "leads"

    business_name = Column(String, nullable=False)
    website = Column(String, nullable=True)
    email = Column(String, nullable=True)
    niche = Column(String, nullable=False)
    region = Column(String, nullable=False)
    fit_score = Column(Integer, nullable=True)
    fit_reason = Column(String, nullable=True)
    draft_outreach = Column(String, nullable=True)
    status = Column(Enum(LeadStatus), default=LeadStatus.draft, nullable=False)
