from pydantic import BaseModel, Field
from typing import List

class EmailResponseModel(BaseModel):
    id: int = Field(..., description="Unique identifier for the email")
    from_: str = Field(..., alias='from', description="Email address or display name of the sender")
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="Body content of the email")
    date: str = Field(..., description="Date when the email was sent (ISO 8601)")
    has_attachments: bool = Field(..., description="Flag indicating if email has attachments")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    
    class Config:
        populate_by_name = True  # Allows using 'from' as alias
        
class SyncResponse(BaseModel):
    status: str
    fetched: int
    inserted: int
    skipped: int
