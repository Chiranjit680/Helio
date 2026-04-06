from langchain_experimental.text_splitter import SemanticChunker
from langchain_huggingface import HuggingFaceEmbeddings  # pip install langchain-huggingface
import requests
import time
EXTRACTION_URL = "http://localhost:8002/api/ocr/extract"

# Wrap your SentenceTransformer model name with LangChain's adapter
embeddings = HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
text_splitter = SemanticChunker(embeddings)


def generate_chunks(file=None, text=None):
    if file is not None:
        response = requests.post(EXTRACTION_URL, json={"doc_path": file})

        if response.status_code != 200:
            raise Exception(f"OCR API failed: {response.text}")

        text = response.json().get("ocr_text", "")
        print(f"OCR extracted text length: {len(text)} characters")

    elif text is None:
        raise ValueError("Either file or text must be provided")

    docs = text_splitter.split_text(text)
    return docs


if __name__ == "__main__":
    start_time = time.time()
    chunks = generate_chunks(file=r"D:\Helio\CV_ChiranjitSaha.pdf")
    end_time = time.time()
    print(f"Chunk generation took {end_time - start_time:.2f} seconds")
    print(f"Generated {len(chunks)} chunks:")
    for i, chunk in enumerate(chunks):
        print(f"Chunk length: {len(chunk)} characters")
        print(f"Chunk {i+1}: {chunk[:100]}...")
        