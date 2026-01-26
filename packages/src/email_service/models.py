from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any

class EmailSearchQuery(BaseModel):
    query: str = Field(..., description="Gmail search query (e.g., 'is:unread', 'from:example@gmail.com')")
    max_results: int = Field(default=10, ge=1, le=100, description="Maximum number of results")

class EmailSendRequest(BaseModel):
    to: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., min_length=1, description="Email subject")
    body: str = Field(..., min_length=1, description="Email body")
    cc: Optional[EmailStr] = Field(None, description="CC recipient")
    bcc: Optional[EmailStr] = Field(None, description="BCC recipient")

class EmailReplyRequest(BaseModel):
    message_id: str = Field(..., description="ID of the message to reply to")
    body: str = Field(..., min_length=1, description="Reply body")

class EmailMarkReadRequest(BaseModel):
    message_id: str = Field(..., description="ID of the message to mark as read")

class EmailDetailsResponse(BaseModel):
    id: str
    subject: str
    from_: str = Field(..., alias="from")
    to: str
    date: str
    body: str
    has_attachments: bool
    labels: List[str]

    class Config:
        populate_by_name = True

class AttachmentInfo(BaseModel):
    filename: str
    size: int

class EmailOperationResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
