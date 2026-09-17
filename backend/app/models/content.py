import enum
from sqlalchemy import Column, Integer, String, ForeignKey, Enum, Boolean, JSON
from sqlalchemy.orm import relationship
from app.models.base import BaseModel

class ContentStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    published = "published"

class ContentAsset(BaseModel):
    __tablename__ = "content_assets"

    brand_id = Column(Integer, ForeignKey("brands.id", ondelete="CASCADE"), nullable=False)
    source_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=True)
    status = Column(Enum(ContentStatus), default=ContentStatus.draft, nullable=False)
    platform = Column(String, nullable=False)
    language = Column(String, default="en", nullable=False)

    brand = relationship("Brand")
    versions = relationship("ContentVersion", back_populates="asset", cascade="all, delete-orphan")
    reviews = relationship("ComplianceReview", back_populates="asset", cascade="all, delete-orphan")

class ContentVersion(BaseModel):
    __tablename__ = "content_versions"

    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False)
    content_text = Column(String, nullable=False)

    asset = relationship("ContentAsset", back_populates="versions")

class ComplianceReview(BaseModel):
    __tablename__ = "compliance_reviews"

    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False)
    passed = Column(Boolean, nullable=False)
    flagged_phrases = Column(JSON, nullable=True)
    reasons = Column(JSON, nullable=True)

    asset = relationship("ContentAsset", back_populates="reviews")

class Feedback(BaseModel):
    __tablename__ = "feedback"

    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False)
    reason_tag = Column(String, nullable=False)
    note = Column(String, nullable=False)
