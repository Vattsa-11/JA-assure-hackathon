from sqlalchemy import Column, Integer, String, ForeignKey
from app.models.base import BaseModel

class VideoAsset(BaseModel):
    __tablename__ = "video_assets"

    content_asset_id = Column(Integer, ForeignKey("content_assets.id", ondelete="CASCADE"), nullable=False)
    topic = Column(String, nullable=True)
    script_text = Column(String, nullable=False)
    video_file_path = Column(String, nullable=True)
