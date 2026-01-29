from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime

class EmailResponseModel(BaseModel):
    id: str=Field(..., description="Unique identifier for the email")
    sender: EmailStr=Field(..., description="Email address of the sender")
    
    subject: str=Field(..., description="Subject of the email")
    body: str=Field(..., description="Body content of the email")
    timestamp: datetime=Field(..., description="Timestamp when the email was sent")
    is_read: bool=Field(..., description="Flag indicating if the email has been read")
