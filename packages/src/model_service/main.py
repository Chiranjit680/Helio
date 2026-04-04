from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    # Works when running as package: python -m model_service.main
    from .routers import router as model_router
    from .model_store import preload_bart_model
except ImportError:
    # Works when running as script: python .\main.py
    from routers import router as model_router
    from model_store import preload_bart_model

app = FastAPI(title="Model Service")

# CORS (optional but useful)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ IMPORTANT: prefix added
app.include_router(model_router, prefix="/api/model")


# Debug: print all routes (remove later)
@app.on_event("startup")
def print_routes():
    print("\nRegistered Routes:")
    for route in app.routes:
        print(route.path)
    preload_ok = preload_bart_model()
    if not preload_ok:
        print("Continuing startup without preloaded BART model")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8004)