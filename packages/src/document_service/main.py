from fastapi import FastAPI
import uvicorn
from routers.upload import router as upload_router

app = FastAPI()

app.include_router(upload_router)

if __name__ == "__main__":  
    
    uvicorn.run(app, host="0.0.0.0", port=8003)
                
