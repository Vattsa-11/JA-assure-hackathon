from sqlalchemy import ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class VideoAsset(BaseModel):
    __tablename__ = "video_assets"

    content_asset_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False
    )
    topic: Mapped[str | None] = mapped_column(String, nullable=True)
    script_text: Mapped[str] = mapped_column(String, nullable=False)
    video_file_path: Mapped[str | None] = mapped_column(String, nullable=True)
