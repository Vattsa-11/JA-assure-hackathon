from pydantic import BaseModel


class ContentRunRequest(BaseModel):
    brand_id: int
    topic: str
    localize: bool = False
    target_languages: list[str] | None = None
    # Optional UI language: generates this campaign natively in the given language
    language: str | None = None

class LeadRunRequest(BaseModel):
    brand_id: int
    niche: str
    region: str
    # Optional UI language: drafts outreach natively in the given language
    language: str | None = None

class VideoRunRequest(BaseModel):
    brand_id: int
    topic: str
    # Optional UI language: writes the video script natively in the given language
    language: str | None = None
    # When true, renders an AI-generated clip (HunyuanVideo via Replicate) as the
    # video background instead of the static gradient. Falls back on failure.
    use_ai_video: bool = False

class ImageRunRequest(BaseModel):
    brand_id: int
    topic: str
    # Optional UI language: writes the image visual brief natively in the given language
    language: str | None = None
