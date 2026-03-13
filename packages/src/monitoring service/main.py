from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
from datetime import datetime
from collections import deque
import uvicorn

app = FastAPI(
    title="Helio Monitoring Service",
    description="Service to monitor the health and performance of Helio services",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Log storage (in-memory for now, can be replaced with database)
logs_storage = deque(maxlen=10000)  # Keep last 10000 logs

class LogEntry(BaseModel):
    service_name: str
    level: str
    message: str
    timestamp: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = {}
    traceback: Optional[str] = None
    correlation_id: Optional[str] = None

services = {
    "email_service": {
        "url": "http://localhost:8001",
        "status": "unknown",
        "last_checked": None
    },
    "data_processing_service": {
        "url": "http://localhost:8002",
        "status": "unknown",
        "last_checked": None
    },
    "notification_service": {
        "url": "http://localhost:8003",    
        "status": "unknown",
        "last_checked": None
    }
}

@app.post("/api/logs")
async def receive_log(log_entry: LogEntry):
    """Receive and store logs from services"""
    try:
        if not log_entry.timestamp:
            log_entry.timestamp = datetime.utcnow().isoformat()
        
        log_dict = log_entry.dict()
        logs_storage.append(log_dict)
        
        # Print to console for debugging
        print(f"[{log_entry.service_name}] [{log_entry.level}] {log_entry.message}")
        if log_entry.traceback:
            print(f"Traceback: {log_entry.traceback}")
        
        return {"status": "success", "message": "Log received"}
    except Exception as e:
        print(f"Error storing log: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/logs")
async def get_logs(
    service_name: Optional[str] = None,
    level: Optional[str] = None,
    limit: int = 100
):
    """Retrieve logs with optional filtering"""
    filtered_logs = list(logs_storage)
    
    if service_name:
        filtered_logs = [log for log in filtered_logs if log.get("service_name") == service_name]
    
    if level:
        filtered_logs = [log for log in filtered_logs if log.get("level") == level]
    
    return {
        "total": len(filtered_logs),
        "logs": filtered_logs[-limit:]
    }

@app.get("/api/logs/errors")
async def get_errors(limit: int = 50):
    """Get all error and critical logs"""
    error_logs = [
        log for log in logs_storage 
        if log.get("level") in ["ERROR", "CRITICAL", "error", "critical"]
    ]
    return {
        "total": len(error_logs),
        "errors": error_logs[-limit:]
    }

@app.get("/api/logs/service/{service_name}")
async def get_service_logs(service_name: str, limit: int = 100):
    """Get logs for a specific service"""
    service_logs = [
        log for log in logs_storage 
        if log.get("service_name") == service_name
    ]
    return {
        "service": service_name,
        "total": len(service_logs),
        "logs": service_logs[-limit:]
    }

@app.delete("/api/logs")
async def clear_logs():
    """Clear all stored logs"""
    logs_storage.clear()
    return {"status": "success", "message": "Logs cleared"}

@app.get("/")
async def root():
    return {
        "service": "Helio Monitoring Service",
        "status": "operational",
        "endpoints": {
            "logs": {
                "post": "/api/logs - Submit logs",
                "get": "/api/logs - Retrieve logs (filter by service_name, level, limit)",
                "errors": "/api/logs/errors - Get error logs only",
                "by_service": "/api/logs/service/{service_name}",
                "clear": "/api/logs (DELETE) - Clear all logs"
            }
        },
        "stats": {
            "total_logs": len(logs_storage),
            "max_capacity": 10000
        }
    }

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🚀 HELIO MONITORING SERVICE STARTING")
    print("="*60)
    print("📊 Endpoints:")
    print("   - POST   /api/logs              (Receive logs)")
    print("   - GET    /api/logs              (Query logs)")
    print("   - GET    /api/logs/errors       (Get errors)")
    print("   - DELETE /api/logs              (Clear logs)")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8004)
