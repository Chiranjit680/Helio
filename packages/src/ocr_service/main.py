from fastapi import FastAPI
from schema import DocumentExtractionSchema
from ocr_extraction import DocumentProcessor, DoclingProcessor, TesseractProcessor, extract_aadhaar_fields, extract_pan_fields
app = FastAPI()

@app.post("/api/ocr/extract")
async def extract_ocr(document: DocumentExtractionSchema):
    document_processor = DocumentProcessor(document.doc_path)
    
    ocr_text = document_processor.extract_text()
    payload = {

        "ocr_text": ocr_text
    }
    
    
    
    return payload
@app.post("/api/ocr/extract/aadhaar")
async def extract_aadhaar(document: DocumentExtractionSchema):
    document_processor = DocumentProcessor(document.doc_path)
    
    ocr_text = document_processor.extract_text()
    aadhaar_data = extract_aadhaar_fields(ocr_text)
    
    return {

        "aadhaar_data": aadhaar_data
    }
@app.post("/api/ocr/extract/pan")
async def extract_pan(document: DocumentExtractionSchema):
    document_processor = DocumentProcessor(document.doc_path)
    
    ocr_text = document_processor.extract_text()
    pan_data = extract_pan_fields(ocr_text)
    
    return {
 
        "pan_data": pan_data
    }
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)
    
    