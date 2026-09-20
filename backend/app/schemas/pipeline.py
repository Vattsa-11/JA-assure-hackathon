from pydantic import BaseModel


class ContentRunRequest(BaseModel):
    brand_id: int
    topic: str
    # Opt-in: also localize every compliance-passed asset (ms/id/th/zh).
    localize: bool = False
    # None/empty -> all supported languages; unknown codes are ignored.
    target_languages: list[str] | None = None

class LeadRunRequest(BaseModel):
    brand_id: int
    niche: str
    region: str

class VideoRunRequest(BaseModel):
    brand_id: int
    topic: str

class ResearchRunRequest(BaseModel):
    urls: list[str]
