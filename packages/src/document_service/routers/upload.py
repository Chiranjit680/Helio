from pathlib import Path
import shutil

from fastapi import APIRouter, File, HTTPException, UploadFile

router = APIRouter(prefix="/upload", tags=["upload"])

UPLOAD_DIR = Path("D:\\Helio\\Helio\\uploads")
PDF_DIR = UPLOAD_DIR / "pdfs"
IMAGE_DIR = UPLOAD_DIR / "images"

PDF_DIR.mkdir(parents=True, exist_ok=True)
IMAGE_DIR.mkdir(parents=True, exist_ok=True)

ALLOWED_PDF_CONTENT_TYPES = {"application/pdf"}
ALLOWED_IMAGE_CONTENT_TYPES = {
	"image/jpeg",
	"image/png",
	"image/webp",
}


def _save_file(file: UploadFile, destination: Path) -> str:
	with open(destination, "wb") as buffer:
		shutil.copyfileobj(file.file, buffer)
	return str(destination)


@router.post("/pdf")
async def upload_pdf(file: UploadFile = File(...)):
	if file.content_type not in ALLOWED_PDF_CONTENT_TYPES:
		raise HTTPException(status_code=400, detail="Only PDF files are allowed")

	file_location = PDF_DIR / file.filename
	saved_path = _save_file(file, file_location)

	return {
		"message": "PDF uploaded successfully",
		"filename": file.filename,
		"content_type": file.content_type,
		"saved_at": saved_path,
	}


@router.post("/image")
async def upload_image(file: UploadFile = File(...)):
	if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
		raise HTTPException(status_code=400, detail="Only image files are allowed")

	file_location = IMAGE_DIR / file.filename
	saved_path = _save_file(file, file_location)

	return {
		"message": "Image uploaded successfully",
		"filename": file.filename,
		"content_type": file.content_type,
		"saved_at": saved_path,
	}

@router.post("/")
async def upload_generic(file: UploadFile = File(...)):
    if file.content_type in ALLOWED_PDF_CONTENT_TYPES:
        return await upload_pdf(file)
    elif file.content_type in ALLOWED_IMAGE_CONTENT_TYPES:
        return await upload_image(file)
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    
    