from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
class EmailResponseModel(BaseModel):
    id: str = Field(..., description="Unique identifier for the email")
    from_: EmailStr = Field(..., alias='from', description="Email address of the sender")
    to: str = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Subject of the email")
    body: str = Field(..., description="Body content of the email")
    date: str = Field(..., description="Date when the email was sent")
    has_attachments: bool = Field(..., description="Flag indicating if email has attachments")
    labels: List[str] = Field(default_factory=list, description="Gmail labels")
    
    class Config:
        populate_by_name = True  # Allows using 'from' as alias