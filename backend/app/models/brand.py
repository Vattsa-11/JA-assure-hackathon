from sqlalchemy import Column, String
from app.models.base import BaseModel

class Brand(BaseModel):
    __tablename__ = "brands"

    name = Column(String, index=True, nullable=False)
    voice_description = Column(String, nullable=False)
