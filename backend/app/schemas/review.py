from pydantic import BaseModel

class RejectRequest(BaseModel):
    reason_tag: str
    note: str

class EditRequest(BaseModel):
    new_content_text: str
