from http import client
from typing import List, Optional
from fastapi import APIRouter, Query, status
from fastapi.concurrency import run_in_threadpool
from google import genai

try:
    from .schema import DocClassificationRequest, DocClassificationResponse, GeminiQuery
    from .model_store import get_or_load_classifier
except ImportError:
    from schema import DocClassificationRequest, DocClassificationResponse, GeminiQuery
    from model_store import get_or_load_classifier
from dotenv import load_dotenv
import os
router = APIRouter(tags=["model_service"])

load_dotenv()  # Load environment variables from .env file
DEFAULT_LABELS = [
    "Finance and accounting",
    "Software development and engineering",
    "Human resources and employee management",
    "Sales and business development",
    "Marketing and branding",
    "Operations and logistics",
    "Legal and compliance",
    "Other"
]


# 🔵 Sync function (CPU-bound work)

def _classify_payload(text: str, candidate_labels: List[str]=DEFAULT_LABELS) -> dict:
    classifier = get_or_load_classifier("valhalla/distilbart-mnli-12-3")

    result = classifier(
        sequences=text,
        candidate_labels=candidate_labels
    )

    return {
        "label": result["labels"][0],
        "score": result["scores"][0]
    }


# 🔵 Async route (non-blocking using threadpool)
@router.post(
    "/classify_docs",
    response_model=DocClassificationResponse,
    status_code=status.HTTP_200_OK
)
async def classify_docs(request: DocClassificationRequest):
    return await run_in_threadpool(
        _classify_payload,
        request.text,
        DEFAULT_LABELS
    )
@router.post(
    "/gemini_interface", status_code=status.HTTP_200_OK
)
async def gemini_interface(request: GeminiQuery):
    
    gemini_api_key=os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=gemini_api_key)

    response = client.models.generate_content(
    model="gemini-3-flash-preview",
    contents=request.text)
    return {"response": response.text}


    

