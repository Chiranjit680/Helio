from pathlib import Path
from email.utils import parsedate_to_datetime

from email_service.email_connector_updated import EmailConnector
import logging
from email_service.email_classifier import email_agent
from email_service.database import get_db
import os
from dotenv import load_dotenv
from email_service.models import EmailRecord
base_dir = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=base_dir / ".env")
from contextlib import closing

def sync_emails():
    connector = EmailConnector(
        credentials_path=os.getenv("GMAIL_CREDENTIALS_PATH", base_dir / "credentials.json"),
        token_path=os.getenv("GMAIL_TOKEN_PATH", base_dir / "storage" / "token.json"),
    )
    logger = logging.getLogger(__name__)
    logger.info("[Scheduler] Starting email sync...")

    connector.connect()
    emails = connector.get_new_emails()

    db_gen = get_db()
    db = next(db_gen)

    try:
        inserted = 0
        skipped = 0

        for msg in emails:
            message_id = msg["id"]

            # ✅ Correct deduplication
            exists = (
                db.query(EmailRecord)
                .filter(EmailRecord.message_id == message_id)
                .first()
            )

            if exists:
                skipped += 1
                continue
            try:
                agent_response = email_agent(
                    email_content=msg["body"],
                    sender_info=msg["from"],
                )
                ai_out = agent_response.dict() if hasattr(agent_response, "dict") else {}
            except Exception:
                ai_out = {}
            raw_date = msg.get("date", None)
            if raw_date:
                try:
                    parsed_date = parsedate_to_datetime(raw_date)
                except Exception:
                    parsed_date = None
            else:
                parsed_date = None
            record = EmailRecord(
                message_id=message_id,
                from_email=msg["from"],
                to_email=msg["to"],
                subject=msg["subject"],
                body=msg["body"],
                date_sent=parsed_date,  # ensure this is datetime
                is_read=False,
                has_attachments=msg.get("has_attachments", False),
                labels= ai_out.get("category"),
                intention= ai_out.get("intent"),
                iu_score=ai_out.get("importance_score"),
                
            )

            db.add(record)
            inserted += 1

        db.commit()
        logger.info(f"[Scheduler] Sync complete | inserted={inserted}, skipped={skipped}")

    except Exception as e:
        db.rollback()
        logger.exception(f"[Scheduler] Sync failed: {e}")

    finally:
        db.close()
