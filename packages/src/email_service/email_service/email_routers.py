
from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import List
import logging
import os
from pathlib import Path
from dotenv import load_dotenv
from email_service.email_classifier import email_agent
from email_service.schema import EmailResponseModel, SyncResponse
from email_service.models import EmailRecord
from email_service.email_connector_updated import EmailConnector
from email_service.database import get_db
load_dotenv()

router = APIRouter(
    prefix="/api/email",
    tags=["email_service"],
)

logger = logging.getLogger("email_service")

credentials_path = Path(os.environ["GMAIL_CREDENTIALS_PATH"]).resolve()
token_path = Path(os.environ["GMAIL_TOKEN_PATH"]).resolve()


def get_connector() -> EmailConnector:
    connector = EmailConnector(
        credentials_path=credentials_path,
        token_path=token_path
    )
    connector.connect()
    return connector


@router.get(
    "/health",
    status_code=status.HTTP_200_OK,
    response_class=JSONResponse
)
async def health_check():
    return {"status": "healthy"}
from pydantic import BaseModel

class SyncResponse(BaseModel):
    status: str
    fetched: int
    inserted: int
    skipped: int


@router.get(
    "/sync",
    response_model=SyncResponse,
    status_code=status.HTTP_200_OK
)
async def sync_emails(
    connector: EmailConnector = Depends(get_connector),
   
    
    db=Depends(get_db)
):
    try:
        emails = connector.get_new_emails()

        inserted = 0
        skipped = 0

        for msg in emails:
            message_id = msg["id"]

            existing = (
                db.query(EmailRecord)
                .filter(EmailRecord.message_id == message_id)
                .first()
            )

            if existing:
                skipped += 1
                continue

            # AI classification (fail-safe)
            try:
                agent_response = email_agent(
                    email_content=msg["body"],
                    sender_info=msg["from"],
                )
                ai_out = agent_response.dict() if hasattr(agent_response, "dict") else {}
            except Exception:
                ai_out = {}

            record = EmailRecord(
                message_id=message_id,
                from_email=msg["from"],
                to_email=msg["to"],
                subject=msg["subject"],
                body=msg["body"],
                date_sent=msg["date"],
                is_read=False,
                labels=ai_out.get("category"),
                iu_score=ai_out.get("importance_score"),
                intention=ai_out.get("intent"),
                has_attachments=msg.get("has_attachments", False),
            )

            db.add(record)
            inserted += 1

        db.commit()

        return {
            "status": "ok",
            "fetched": len(emails),
            "inserted": inserted,
            "skipped": skipped,
        }

    except Exception:
        logger.exception("Error syncing emails")
        raise HTTPException(status_code=500, detail="Failed to sync emails")

@router.get("/unread", response_model=List[EmailResponseModel], status_code=status.HTTP_200_OK)
async def get_unread_emails(
    db=Depends(get_db)
):
    """Fetch unread emails from the database."""
    try:
        records= (db.query(EmailRecord).filter(EmailRecord.is_read == False).all())
        
        db.query(EmailRecord).filter(EmailRecord.is_read == False).update({"is_read": True})
        db.commit()
        
        return [{
            "id" : r.id,
            "from": r.from_email,
            "to": r.to_email,
            "subject": r.subject,
            "body": r.body,
            "date": r.date_sent.isoformat() if r.date_sent else None,
            "has_attachments": r.has_attachments,
            "labels": r.labels.split(",") if r.labels else []
            
        }
            
        for r in records]
    except Exception:
        logger.exception("Error fetching unread emails")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch unread emails"
        )
@router.get("/all",
   response_model=List[EmailResponseModel],
    status_code=status.HTTP_200_OK  
)
async def get_all_emails(
    db=Depends(get_db)
):
    """Fetch all emails from the database."""
    try:
        records = db.query(EmailRecord).limit(10).all()
        return [{
            "id": r.id,
            "from": r.from_email,
            "to": r.to_email,
            "subject": r.subject,
            "body": r.body,
            "date": r.date_sent.isoformat() if r.date_sent else None,
            "has_attachments": r.has_attachments,
            "labels": r.labels.split(",") if r.labels else []
        } for r in records]
    except Exception:
        logger.exception("Error fetching all emails")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch all emails"
        )

    

@router.get("/important",
            response_model=List[EmailResponseModel],
    status_code=status.HTTP_200_OK  
)
async def get_important_emails(
    db=Depends(get_db)
):
    """Fetch important emails from the database."""
    try:
        records = (db.query(EmailRecord)
                   .filter(EmailRecord.iu_score >= 3)
                   .order_by(EmailRecord.iu_score.desc())
                   .limit(10)
                   .all())
        return [{
            "id": r.id,
            "from": r.from_email,
            "to": r.to_email,
            "subject": r.subject,
            "body": r.body,
            "date": r.date_sent.isoformat() if r.date_sent else None,
            "has_attachments": r.has_attachments,
            "labels": r.labels.split(",") if r.labels else []
        } for r in records]
    except Exception:
        logger.exception("Error fetching important emails")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch important emails"
        )
    
    
@router.post("/admin/init-db", status_code=status.HTTP_200_OK)
async def admin_init_db():
    """Admin endpoint to initialize DB tables (useful in local/dev)."""
    try:
        from email_service.database import init_db
        init_db()
        return {"status": "ok", "detail": "DB tables created or already exist"}
    except Exception as e:
        logger.exception("DB init failed")
        raise HTTPException(status_code=500, detail=str(e))
