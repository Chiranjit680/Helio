from collections import deque
from pathlib import Path
import shutil
import sys

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.concurrency import run_in_threadpool

SRC_DIR = Path(__file__).resolve().parents[2]
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from model_service.classify_payload_semantic import _classify_payload_semantic
from knowledge_base import DocumentProcessor
from sync_knowledge_base import task, push_to_queue

# =========================
# Router
# =========================
router = APIRouter(prefix="/upload", tags=["upload"])


# =========================
# Constants
# =========================
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

ALLOWED_PDF_CONTENT_TYPES   = {"application/pdf"}
ALLOWED_IMAGE_CONTENT_TYPES = {"image/jpeg", "image/png", "image/webp"}

 # In-memory queue for updates (for demonstration)   
# =========================
# Directory Layout
# =========================
BASE_DIR = Path("uploads")

LABEL_DIR_MAP = {
    "Software development and engineering":    BASE_DIR / "Engineering_docs",
    "Human resources and employee management": BASE_DIR / "HR_docs",
    "Finance and accounting":                  BASE_DIR / "Finance_docs",
    "Legal and compliance":                    BASE_DIR / "Legal_docs",
    "Marketing and branding":                  BASE_DIR / "Marketing_docs",
    "Sales and business development":          BASE_DIR / "Sales_docs",
    "Operations and logistics":                BASE_DIR / "Operations_docs",
    "Other":                                   BASE_DIR / "Other_docs",
}

for _dir in LABEL_DIR_MAP.values():
    (_dir / "pdf").mkdir(parents=True, exist_ok=True)
    (_dir / "images").mkdir(parents=True, exist_ok=True)


# =========================
# PDF Upload
# =========================

@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_PDF_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF files are allowed")

    # 1. Read + extract text
    doc_processor = DocumentProcessor()
    file_content = await file.read()
    if not file_content:
        raise HTTPException(status_code=400, detail="Uploaded PDF could not be read or is empty.")
    text = await run_in_threadpool(doc_processor.extract_text, file_content)
    if not text:
        raise HTTPException(
            status_code=422,
            detail="No extractable text was found in the uploaded PDF.",
        )

    # 2. Classify
    result     = await run_in_threadpool(_classify_payload_semantic, text)
    label      = result["label"]
    confidence = result["score"]

    # 3. Save PDF to classified folder
    pdf_dir    = LABEL_DIR_MAP.get(label, LABEL_DIR_MAP["Other"]) / "pdf"
    saved_path = pdf_dir / file.filename
    with open(saved_path, "wb") as f:
        f.write(file_content)
    
    push_to_queue({"filename": file.filename, "label": label, "type": "pdf"})
    return {
        "message"    : "PDF uploaded and classified",
        "filename"   : file.filename,
        "label"      : label,
        "confidence" : confidence,
        "saved_at"   : str(saved_path),
    }


# =========================
# Image Upload
# =========================

@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
    if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
        raise HTTPException(status_code=400, detail="Only image files are allowed")

    # 1. Classify by filename
    result     = await run_in_threadpool(_classify_payload_semantic, file.filename)
    label      = result["label"]
    confidence = result["score"]

    # 2. Save image to classified folder
    image_dir  = LABEL_DIR_MAP.get(label, LABEL_DIR_MAP["Other"]) / "images"
    saved_path = image_dir / file.filename

    with open(saved_path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    file_content = 

    push_to_queue({"filename": file.filename,  "label": label, "type": "image"})

    return {
        "message"   : "Image uploaded and classified",
        "filename"  : file.filename,
        "label"     : label,
        "confidence": confidence,
        "saved_at"  : str(saved_path),
    }


# =========================
# Generic Upload
# =========================

@router.post("/")
async def upload_generic(file: UploadFile = File(...)):
    if file.content_type in ALLOWED_PDF_CONTENT_TYPES:
        return await upload_pdf(file)
    elif file.content_type in ALLOWED_IMAGE_CONTENT_TYPES:
        return await upload_image(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")