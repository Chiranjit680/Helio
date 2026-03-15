
from pydantic import BaseModel, Field
from typing import List

class DocumentExtractionSchema(BaseModel):
    doc_path: str= Field(..., description="File path to the document for OCR processing")
