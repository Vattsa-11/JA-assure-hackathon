from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import BaseModel


class Brand(BaseModel):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String, index=True, nullable=False)
    voice_description: Mapped[str] = mapped_column(String, nullable=False)
    color: Mapped[str] = mapped_column(String, default="#202020")
