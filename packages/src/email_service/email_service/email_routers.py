from fastapi import APIRouter, HTTPException, status, Depends
from fastapi.responses import JSONResponse
from typing import List
import logging
import os
from pathlib import Path
from dotenv import load_dotenv

from email_service.models import EmailResponseModel
from email_service.email_connector_updated import EmailConnector

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


@router.get(
    "/unread",
    response_model=List[EmailResponseModel],
    status_code=status.HTTP_200_OK
)
async def get_unread_emails(
    connector: EmailConnector = Depends(get_connector)
):
    try:
        return connector.get_new_emails()
    except Exception as e:
        logger.exception("Error fetching unread emails")
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch unread emails"
        )
