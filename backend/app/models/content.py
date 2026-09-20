import enum

from sqlalchemy import JSON, Boolean, Enum, ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import BaseModel
from app.models.brand import Brand


class ContentStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    published = "published"


class ContentAsset(BaseModel):
    __tablename__ = "content_assets"

    brand_id: Mapped[int] = mapped_column(
        ForeignKey("brands.id", ondelete="CASCADE"), nullable=False
    )
    source_asset_id: Mapped[int | None] = mapped_column(
        ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=True
    )
    topic: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[ContentStatus] = mapped_column(
        Enum(ContentStatus), default=ContentStatus.draft, nullable=False
    )
    platform: Mapped[str] = mapped_column(String, nullable=False)
    language: Mapped[str] = mapped_column(String, default="en", nullable=False)

    brand: Mapped["Brand"] = relationship("Brand")
    versions: Mapped[list["ContentVersion"]] = relationship(
        "ContentVersion", back_populates="asset", cascade="all, delete-orphan"
    )
    reviews: Mapped[list["ComplianceReview"]] = relationship(
        "ComplianceReview", back_populates="asset", cascade="all, delete-orphan"
    )


class ContentVersion(BaseModel):
    __tablename__ = "content_versions"

    content_asset_id: Mapped[int] = mapped_column(
        ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    content_text: Mapped[str] = mapped_column(String, nullable=False)

    asset: Mapped[ContentAsset] = relationship(
        "ContentAsset", back_populates="versions"
    )


class ComplianceReview(BaseModel):
    __tablename__ = "compliance_reviews"

    content_asset_id: Mapped[int] = mapped_column(
        ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    passed: Mapped[bool] = mapped_column(Boolean, nullable=False)
    flagged_phrases: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)
    reasons: Mapped[list[str] | None] = mapped_column(JSON, nullable=True)

    asset: Mapped[ContentAsset] = relationship(
        "ContentAsset", back_populates="reviews"
    )


class Feedback(BaseModel):
    __tablename__ = "feedback"

    content_asset_id: Mapped[int] = mapped_column(
        ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    reason_tag: Mapped[str] = mapped_column(String, nullable=False)
    note: Mapped[str] = mapped_column(String, nullable=False)
