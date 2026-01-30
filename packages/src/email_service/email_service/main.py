from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from email_service.email_connector_updated import EmailConnector
from email_service.email_routers import router as email_router
from apscheduler.schedulers.background import BackgroundScheduler
from email_service.background_process import sync_emails
scheduler= BackgroundScheduler()
app= FastAPI(
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
@app.on_event("startup")
async def startup_event():
    print("Email Service is starting up...")

    # Initialize DB tables if they don't exist
    try:
        from email_service.database import init_db
        init_db()
        print("Database tables ensured.")
        scheduler.add_job(
            func=sync_emails,
            trigger="interval",
            minutes=5,
            id="email_sync_job",
            replace_existing=True)
        scheduler.start()
        
    except Exception as e:
        print(f"Database initialization failed: {e}")

    credentials_path = os.getenv("GMAIL_CREDENTIALS_PATH", BASE_DIR / "credentials.json")
    token_path = os.getenv("GMAIL_TOKEN_PATH", BASE_DIR / "storage" /
                            "token.json")
    init_connector= EmailConnector(
        credentials_path=credentials_path,
        token_path=token_path)
    print("Email Connector initialized.")
@app.on_event("shutdown")
async def shutdown_event():
    print("Email Service is shutting down...")
    
@app.get("/")
async def root():
    return {"message": "Welcome to the Helio Email Service!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)