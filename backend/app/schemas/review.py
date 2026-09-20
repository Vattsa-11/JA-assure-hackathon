
from pydantic import BaseModel


class LeadSchema(BaseModel):
    id: int
    business_name: str
    website: str | None = None
    email: str | None = None
    niche: str
    region: str
    fit_score: int | None = None
    fit_reason: str | None = None
    draft_outreach: str | None = None
    status: str

    class Config:
        from_attributes = True

class RejectRequest(BaseModel):
    reason_tag: str
    note: str

class EditRequest(BaseModel):
    new_content_text: str
