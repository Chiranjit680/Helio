# OCR Extraction Service

This service provides OCR (Optical Character Recognition) functionality using Tesseract.

## Prerequisites

1. **Install Tesseract OCR:**
   - **Windows:** Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki) or use: `choco install tesseract`
   - **Mac:** `brew install tesseract`
   - **Linux:** `sudo apt-get install tesseract-ocr`

2. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Poppler (for PDF support):**
   - **Windows:** Download from [here](https://github.com/oschwartz10612/poppler-windows/releases/) and add to PATH
   - **Mac:** `brew install poppler`
   - **Linux:** `sudo apt-get install poppler-utils`

## Usage

### Basic Text Extraction

```python
from ocr_extraction import extract_text

# Extract text from image
text = extract_text('document.png')
print(text)
```

### Advanced Usage

```python
from ocr_extraction import TesseractOCR

# Initialize OCR
ocr = TesseractOCR(lang='eng')

# Extract text with preprocessing
text = ocr.extract_text_from_image('document.jpg', preprocess=True)

# Extract with bounding boxes
boxes = ocr.extract_text_with_boxes('document.png')
for box in boxes:
    print(f"Text: {box['text']}, Confidence: {box['confidence']}%")
    print(f"Position: ({box['left']}, {box['top']})")

# Extract from PDF
pages = ocr.extract_text_from_pdf('document.pdf', dpi=300)
for i, page_text in enumerate(pages):
    print(f"Page {i+1}:\n{page_text}\n")

# Get confidence score
confidence = ocr.get_confidence_score('document.png')
print(f"OCR Confidence: {confidence}%")
```

### Custom Configuration

```python
# Custom Tesseract path
ocr = TesseractOCR(
    tesseract_cmd='C:/Program Files/Tesseract-OCR/tesseract.exe',
    lang='eng'
)

# Custom PSM (Page Segmentation Mode)
# PSM values:
#   0 = Orientation and script detection (OSD) only
#   1 = Automatic page segmentation with OSD
#   3 = Fully automatic page segmentation, but no OSD (Default)
#   6 = Assume a single uniform block of text
#   11 = Sparse text. Find as much text as possible in no particular order
text = ocr.extract_text_from_image('document.png', config='--psm 11')
```

### Multiple Languages

```python
# Multiple languages (e.g., English + French)
ocr = TesseractOCR(lang='eng+fra')
text = ocr.extract_text_from_image('multilingual_doc.png')
```

## Features

- ✅ Extract text from images (PNG, JPG, TIFF, etc.)
- ✅ Extract text from PDF documents
- ✅ Image preprocessing (grayscale, threshold, denoise, deskew)
- ✅ Bounding box detection
- ✅ Confidence scores
- ✅ Multi-language support
- ✅ Configurable OCR parameters

## Supported Image Formats

- PNG, JPG, JPEG, TIFF, BMP, GIF, WebP

## Tips for Better OCR Results

1. Use high-resolution images (300 DPI recommended)
2. Ensure good contrast between text and background
3. Use preprocessing for noisy or skewed images
4. Choose appropriate PSM mode for your document layout
5. Use language-specific training data when available
