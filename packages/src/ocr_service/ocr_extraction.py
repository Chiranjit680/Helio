import pytesseract
import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
from docling.document_converter import DocumentConverter
import re
from typing import Optional, Dict


pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"


class DoclingProcessor:

    def __init__(self, doc_path):
        self.doc_path = str(doc_path)

    def extract_text(self):
        try:
            converter = DocumentConverter()
            doc = converter.convert(self.doc_path).document
            return doc.export_to_markdown()
        except Exception as e:
            print(f"Docling OCR error: {e}")
            return None


class TesseractProcessor:

    def __init__(self, doc_path):
        self.doc_path = str(doc_path)

    def image_text_extraction(self):
        try:
            img = Image.open(self.doc_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            print(f"Tesseract OCR error: {e}")
            return None

    def extract_text(self):
        extension = Path(self.doc_path).suffix.lower()

        if extension == ".pdf":
            pages = convert_from_path(self.doc_path)

            text_by_page = []
            for page in pages:
                text_by_page.append(
                    pytesseract.image_to_string(page, config="--oem 3 --psm 6")
                )

            return "\n".join(text_by_page)

        return self.image_text_extraction()


class DocumentProcessor:

    def __init__(self, doc_path, ocr_tool="docling"):
        self.doc_path = str(doc_path)

        if ocr_tool == "docling":
            self.processor = DoclingProcessor(self.doc_path)
        else:
            self.processor = TesseractProcessor(self.doc_path)

    @staticmethod
    def upload_image(file):

        extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported image extension: {extension}")

        upload_dir = Path(r"D:\Helio\Helio\Assets\Image documents")
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_path = upload_dir / Path(file.filename).name

        with open(temp_path, "wb") as f:
            f.write(file.read())

        return str(temp_path)

    @staticmethod
    def upload_pdf(file):

        extension = os.path.splitext(file.filename)[1].lower()

        if extension != ".pdf":
            raise ValueError(f"Unsupported PDF extension: {extension}")

        upload_dir = Path(r"D:\Helio\Helio\Assets\PDF documents")
        upload_dir.mkdir(parents=True, exist_ok=True)

        temp_path = upload_dir / Path(file.filename).name

        with open(temp_path, "wb") as f:
            f.write(file.read())

        return str(temp_path)

    def extract_text(self):
        return self.processor.extract_text()


def extract_pan_fields(ocr_text: str) -> Dict[str, Optional[str]]:
    # Normalize whitespace/newlines for more stable regex matching
    text = re.sub(r"[ \t]+", " ", ocr_text.replace("\r", "\n"))

    # 1) PAN number: 5 letters + 4 digits + 1 letter
    pan_match = re.search(r"\b([A-Z]{5}[0-9]{4}[A-Z])\b", text, flags=re.IGNORECASE)
    pan_no = pan_match.group(1).upper() if pan_match else None

    # 2) Name from labeled patterns (supports '/Name', 'Name', with next/previous line)
    name = None
    name_patterns = [
        r"(?im)^\s*([A-Z][A-Z .]{2,})\s*$\n\s*/?\s*Name\b",      # value line then /Name
        r"(?im)\b/?:?\s*Name\b\s*[:\-]?\s*([A-Z][A-Z .]{2,})",  # Name: VALUE
    ]
    for p in name_patterns:
        m = re.search(p, text)
        if m:
            name = " ".join(m.group(1).split()).strip()
            break

    # 3) Father's name from labeled patterns
    father_name = None
    father_patterns = [
        r"(?im)^\s*([A-Z][A-Z .]{2,})\s*$\n\s*/?\s*Father'?s?\s*Name\b",
        r"(?im)\bFather'?s?\s*Name\b\s*[:\-]?\s*([A-Z][A-Z .]{2,})",
    ]
    for p in father_patterns:
        m = re.search(p, text)
        if m:
            father_name = " ".join(m.group(1).split()).strip()
            break

    # 4) Fallback when labels are messy/missing: pick uppercase person-like lines
    if not name or not father_name:
        blacklist = {
            "INCOME TAX DEPARTMENT",
            "PERMANENT ACCOUNT NUMBER CARD",
            "GOVT OF INDIA",
            "GOVERNMENT OF INDIA",
            "NAME",
            "FATHER'S NAME",
            "FATHERS NAME",
        }

        candidates = []
        for line in text.split("\n"):
            line = re.sub(r"[^A-Z .]", "", line.upper()).strip()
            if len(line) < 3:
                continue
            if line in blacklist:
                continue
            if re.fullmatch(r"[A-Z][A-Z .]{2,}", line):
                if line not in candidates:
                    candidates.append(line)

        if not name and candidates:
            name = candidates[0].title()
        if not father_name and len(candidates) > 1:
            # second distinct candidate often corresponds to father's name
            father_name = candidates[1].title()

    return {
        "name": name,
        "pan_no": pan_no,
        "father_name": father_name
    }


def extract_aadhaar_fields(ocr_text: str) -> Dict[str, Optional[str]]:
    """
    Extract key Aadhaar fields from noisy OCR text:
    - name
    - dob (DD/MM/YYYY)
    - gender (Male/Female/Other)
    - aadhaar_no (12 digits, returned as XXXX XXXX XXXX)
    """
    # Normalize OCR text
    text = ocr_text.replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)

    # ---------- Aadhaar number ----------
    # Matches: 123412341234 or 1234 1234 1234
    aadhaar_match = re.search(r"\b(\d{4}\s?\d{4}\s?\d{4})\b", text)
    aadhaar_no = None
    if aadhaar_match:
        digits = re.sub(r"\D", "", aadhaar_match.group(1))
        if len(digits) == 12:
            aadhaar_no = f"{digits[0:4]} {digits[4:8]} {digits[8:12]}"

    # ---------- DOB ----------
    # Handles OCR variants like:
    # Date of Birth: 12/04/1984
    # DateolBit/D0B:12/04/1984
    dob_match = re.search(
        r"(?i)(?:date\s*of\s*birth|dob|d0b|dateolbit)\s*[:\-]?\s*(\d{2}[/-]\d{2}[/-]\d{4})",
        text
    )
    dob = dob_match.group(1).replace("-", "/") if dob_match else None

    # ---------- Gender ----------
    gender_match = re.search(r"(?i)\b(male|female|other)\b", text)
    gender = gender_match.group(1).capitalize() if gender_match else None

    # ---------- Name ----------
    # Preferred: text before DOB on same line
    name = None
    name_before_dob = re.search(
        r"(?im)^\s*([A-Z][A-Za-z .]{2,}?)\s+.*?(?:date\s*of\s*birth|dob|d0b|dateolbit)\b",
        text
    )
    if name_before_dob:
        name = " ".join(name_before_dob.group(1).split())

    # Fallback: pick first person-like line (avoid common non-name lines)
    if not name:
        blacklist_tokens = [
            "government", "goyemment", "india", "aadhaar", "identity",
            "citizenship", "birth", "female", "male", "dob", "date"
        ]
        for line in text.split("\n"):
            cleaned = re.sub(r"[^A-Za-z .]", " ", line)
            cleaned = " ".join(cleaned.split()).strip()
            if len(cleaned) < 3:
                continue
            low = cleaned.lower()
            if any(tok in low for tok in blacklist_tokens):
                continue
            # 2-4 words, likely person name
            if re.fullmatch(r"[A-Za-z]+(?: [A-Za-z]+){1,3}", cleaned):
                name = cleaned.title()
                break

    return {
        "name": name,
        "dob": dob,
        "gender": gender,
        "aadhaar_no": aadhaar_no
    }

def main():

    path = r"D:\Helio\Helio\Assets\Image documents\aadhar-demo.png"

    processor = DocumentProcessor(path, ocr_tool="docling")

    extracted_text = processor.extract_text()

    print("\n===== Extracted Text =====\n")
    print(extracted_text)
    print("\n===== Extracted Fields =====\n")
    fields = extract_aadhaar_fields(extracted_text)
    print(fields)



if __name__ == "__main__":
    main()