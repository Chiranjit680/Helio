from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from email_service.email_knowledge_base import sync_postgres_to_chroma
from email_service.email_connector_updated import EmailConnector
from email_service.email_routers import router as email_router
from apscheduler.schedulers.background import BackgroundScheduler
from email_service.background_process import sync_emails

# === MONITORING IMPORT (disabled) ===
# from email_service.monitoring_logger import setup_monitoring_logger

# === MONITORING HTTP CLIENT (disabled) ===
# import requests

import logging
from email_classifier import preload_model
from email_knowledge_base import chroma_client, collection, sync_postgres_to_chroma

scheduler = BackgroundScheduler()

# === MONITORING LOGGER SETUP (disabled) ===
# email_logger = setup_monitoring_logger(
#     service_name="email_service",
#     monitoring_url="http://localhost:8004/api/logs",
#     log_level=logging.INFO
# )

# Fallback: standard console logger
email_logger = logging.getLogger("email_service")
if not email_logger.handlers:
    _handler = logging.StreamHandler()
    _handler.setFormatter(logging.Formatter(
        fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S"
    ))
    email_logger.addHandler(_handler)
email_logger.setLevel(logging.INFO)

app = FastAPI(
    title="Helio Email Service",
    description="Service to handle email operations using Gmail API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(email_router)

from pathlib import Path
import os
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
load_dotenv(dotenv_path=BASE_DIR / ".env")


def run_sync():
    try:
        sync_emails()
        sync_postgres_to_chroma()
        email_logger.info("Initial email sync and ChromaDB sync completed successfully.")
    except Exception as e:
        email_logger.error(f"Error during initial sync: {e}", exc_info=True)


@app.on_event("startup")
async def startup_event():
    email_logger.info("Email Service is starting up...")

    try:
        preload_model()
        email_logger.info("Email classification model preloaded successfully")
    except Exception as e:
        email_logger.error(f"Failed to preload email classification model: {e}", exc_info=True)

    try:
        from email_service.database import init_db
        init_db()
        email_logger.info("Database tables ensured.")

        scheduler.add_job(
            func=run_sync,
            trigger="interval",
            minutes=1,
            id="email_sync_job",
            replace_existing=True
        )
        scheduler.start()
        email_logger.info("Background scheduler started for email sync")

    except Exception as e:
        email_logger.error(f"Failed to start background scheduler: {e}", exc_info=True)

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", BASE_DIR / "credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", BASE_DIR / "storage" / "token.json")

    try:
        init_connector = EmailConnector(
            credentials_path=credentials_path,
            token_path=token_path
        )
        email_logger.info("Email Connector initialized successfully")
    except Exception as e:
        email_logger.error(f"Failed to initialize Email Connector: {e}", exc_info=True)


@app.on_event("shutdown")
async def shutdown_event():
    email_logger.info("Email Service is shutting down...")
    try:
        scheduler.shutdown()
        email_logger.info("Scheduler stopped")
    except Exception as e:
        email_logger.error(f"Error shutting down scheduler: {e}", exc_info=True)


@app.get("/")
async def root():
    return {"message": "Welcome to the Helio Email Service!"}


if __name__ == "__main__":
    import uvicorn
    try:
        email_logger.info("Starting Email Service on port 8001")
        uvicorn.run(app, host="0.0.0.0", port=8001)
    except Exception as e:
        email_logger.critical(f"Email Service crashed: {e}", exc_info=True)