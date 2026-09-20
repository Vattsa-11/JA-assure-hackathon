from pydantic import BaseModel
from typing import Optional

class LeadSchema(BaseModel):
    id: int
    business_name: str
    website: Optional[str] = None
    email: Optional[str] = None
    niche: str
    region: str
    fit_score: Optional[int] = None
    fit_reason: Optional[str] = None
    draft_outreach: Optional[str] = None
    status: str

    class Config:
        from_attributes = True

class RejectRequest(BaseModel):
    reason_tag: str
    note: str

class EditRequest(BaseModel):
    new_content_text: str
