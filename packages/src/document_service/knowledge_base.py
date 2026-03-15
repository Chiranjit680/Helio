
import requests


image_extraction_url = "http://localhost:8002/api/ocr/extract"

def extract_text_from_image(image_path):
    try:
        response = requests.post(image_extraction_url, json={"doc_path": str(image_path)})
        print("Response from OCR service:", response.json())
        return response.json().get("extracted_text")
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None
if __name__ == "__main__":
    test_image_path = "D:\\Helio\\Helio\\Assets\\Image documents\\AADHAR demo.jpeg"
    extracted_text = extract_text_from_image(test_image_path)
    print("Extracted Text:", extracted_text)