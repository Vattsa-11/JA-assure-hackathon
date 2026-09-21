from pydantic import BaseModel

class ContentRunRequest(BaseModel):
    brand_id: int
    topic: str

class LeadRunRequest(BaseModel):
    brand_id: int
    niche: str
    region: str

class VideoRunRequest(BaseModel):
    brand_id: int
    topic: str

class ResearchRunRequest(BaseModel):
    urls: list[str]
