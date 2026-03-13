import pytesseract
import os
from pathlib import Path
from pdf2image import convert_from_path
from PIL import Image
import pytesseract

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

class DocsProcessor:

    def __init__(self, doc_path):
        self.doc_path = str(doc_path)

    @staticmethod
    def upload_image(file):
        """Save an uploaded image file to the image assets directory."""
        extension = os.path.splitext(file.filename)[1].lower()
        allowed_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff"}

        if extension not in allowed_extensions:
            raise ValueError(f"Unsupported image extension: {extension}")

        upload_dir = Path(r"D:\Helio\Helio\Assets\Image documents")
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(file.filename).name
        temp_path = upload_dir / safe_name

        with open(temp_path, "wb") as f:
            f.write(file.read())

        return str(temp_path)

    @staticmethod
    def upload_pdf(file):
        """Save an uploaded PDF file to the PDF assets directory."""
        extension = os.path.splitext(file.filename)[1].lower()

        if extension != ".pdf":
            raise ValueError(f"Unsupported PDF extension: {extension}")

        upload_dir = Path(r"D:\Helio\Helio\Assets\PDF documents")
        upload_dir.mkdir(parents=True, exist_ok=True)

        safe_name = Path(file.filename).name
        temp_path = upload_dir / safe_name

        with open(temp_path, "wb") as f:
            f.write(file.read())

        return str(temp_path)

    def extract_text(self):
        """Extract text from an image using Tesseract."""
        try:
            img = Image.open(self.doc_path)
            return pytesseract.image_to_string(img)
        except Exception as e:
            print(f"Error during OCR extraction: {e}")
            return None

    def process_document(self):
        """Process either an image or PDF and return extracted text."""
        extension = Path(self.doc_path).suffix.lower()

        if extension == ".pdf":
            pages = convert_from_path(self.doc_path)

            text_by_page = []
            for page in pages:
                text_by_page.append(pytesseract.image_to_string(page, config='--oem 3 --psm 6'))

            return "\n".join(text_by_page)

        return self.extract_text()


def main():

    # Path to the document you want to test
    path = r"D:\Helio\Helio\Assets\Image documents\PAN card.jpeg"

    processor = DocsProcessor(path)

    extension = Path(path).suffix.lower()

    if extension == ".pdf":
        extracted_text = processor.process_document()
    else:
        extracted_text = processor.extract_text()

    print("\n===== Extracted Text =====\n")
    print(extracted_text)


if __name__ == "__main__":
    main()