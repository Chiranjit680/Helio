from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean
from sqlalchemy.sql import func

from email_service.database import Base

class EmailRecord(Base):
    __tablename__ = "emails"

    id = Column(Integer, primary_key=True, index=True)

    message_id = Column(String, unique=True, index=True, nullable=False)

    from_email = Column(String, index=True)
    to_email = Column(String, index=True)

    subject = Column(String, index=True)
    body = Column(Text)

    date_sent = Column(DateTime, index=True)
    labels = Column(String)  # Comma-separated labels
    iu_score = Column(Integer, default=0)  # Importance/Urgency score
    has_attachments = Column(Boolean, default=False)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    intention = Column(String, index=True)  
