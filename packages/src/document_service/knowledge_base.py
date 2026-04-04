import os
from collections import deque
from uuid import uuid4

import requests
from dotenv import load_dotenv
from huggingface_hub import InferenceClient
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_experimental.text_splitter import SemanticChunker
import chromadb
from chromadb.config import Settings

load_dotenv()

# =========================
# Constants
# =========================
EXTRACTION_URL  = "http://localhost:8002/api/ocr/extract"
HF_MODEL        = "sentence-transformers/all-MiniLM-L6-v2"
LLM_MODEL       = "meta-llama/Meta-Llama-3-8B-Instruct"
CONTEXT_WINDOW  = 10   # chunks before/after for context generation


# =========================
# Embedder + Splitter
# =========================
_embedder = HuggingFaceEmbeddings(model_name=HF_MODEL)

_splitter = SemanticChunker(
    embeddings=_embedder,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=90,
)


# =========================
# ChromaDB — one client per label (lazy, via helper)
# =========================
LABEL_COLLECTION_MAP = {
    "Software development and engineering":    ("Engineering_docs",  "engineering_docs"),
    "Human resources and employee management": ("HR_docs",           "hr_docs"),
    "Finance and accounting":                  ("Finance_docs",       "finance_docs"),
    "Legal and compliance":                    ("Legal_docs",         "legal_docs"),
    "Marketing and branding":                  ("Marketing_docs",     "marketing_docs"),
    "Sales and business development":          ("Sales_docs",         "sales_docs"),
    "Operations and logistics":                ("Operations_docs",    "operations_docs"),
    "Other":                                   ("Other_docs",         "other_docs"),
}

_chroma_clients: dict[str, chromadb.Collection] = {}

def _get_collection(label: str) -> chromadb.Collection:
    """Return (and cache) the ChromaDB collection for the given label."""
    if label not in _chroma_clients:
        folder, collection_name = LABEL_COLLECTION_MAP.get(
            label, LABEL_COLLECTION_MAP["Other"]
        )
        path   = f"./uploads/{folder}/chroma_store"
        client = chromadb.PersistentClient(
            path=path,
            settings=Settings(anonymized_telemetry=False),
        )
        _chroma_clients[label] = client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"},
        )
    return _chroma_clients[label]


# =========================
# Context generation via LLM
# =========================
def generate_context(pretext: list[str], chunk: str, posttext: list[str]) -> str:
    """
    Ask the LLM to produce a short contextual description of `chunk`
    given the surrounding chunks as context.
    """
    surrounding = "\n\n".join(pretext + [chunk] + posttext)

    system_prompt = (
        "You are a helpful assistant that situates document chunks for retrieval. "
        "Given the surrounding document context and a focal chunk, write a single short "
        "sentence that describes what the chunk is about. Output only that sentence."
    )
    user_prompt = (
        f"<document_context>\n{surrounding}\n</document_context>\n\n"
        f"<chunk>\n{chunk}\n</chunk>\n\n"
        "Provide a short succinct context sentence for this chunk."
    )

    client = InferenceClient(
        model=LLM_MODEL,
        token=os.getenv("HUGGINGFACE_API_KEY"),
    )

    response = client.chat_completion(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": user_prompt},
        ],
        max_tokens=100,
    )
    return response.choices[0].message.content.strip()


# =========================
# Document Processor
# =========================
class DocumentProcessor:

    # ---- Text extraction ------------------------------------------------

    def extract_text(self, path: str) -> str | None:
        try:
            print("trying to extract text from", path)
            resp = requests.post(EXTRACTION_URL, json={"doc_path": str(path)}, timeout=30)
            resp.raise_for_status()
            return resp.json().get("extracted_text")
        except Exception as e:
            print(f"[extract_text] Error: {e}")
            return None

    # ---- Core ingestion pipeline ----------------------------------------

    def _ingest_chunks(self, chunks: list[str], label: str, filename: str) -> int:
        """
        For every chunk:
          1. Build ±CONTEXT_WINDOW sliding window
          2. Generate LLM context description
          3. Enrich  = context + chunk
          4. Embed the enriched text
          5. Store in the correct ChromaDB collection

        Returns the number of chunks stored.
        """
        collection = _get_collection(label)

        ids, embeddings, documents, metadatas = [], [], [], []

        for i, chunk in enumerate(chunks):
            # Sliding window (lists of strings, not joined yet — passed to LLM)
            pre  = chunks[max(0, i - CONTEXT_WINDOW) : i]
            post = chunks[i + 1 : i + 1 + CONTEXT_WINDOW]

            # LLM-generated context
            context = generate_context(pre, chunk, post)

            # Enriched text: context description prepended to raw chunk
            enriched = f"{context}\n\n{chunk}"

            # Embed enriched text
            embedding = _embedder.embed_query(enriched)

            ids.append(str(uuid4()))
            embeddings.append(embedding)
            documents.append(enriched)
            metadatas.append({
                "filename":    filename,
                "label":       label,
                "chunk_index": i,
                "raw_chunk":   chunk,   # stored for clean display at query time
            })

        collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas,
        )
        return len(chunks)

    # ---- Queue consumer -------------------------------------------------

    def update_knowledge_base(self) -> None:
        from routers.upload import LABEL_DIR_MAP, update_queue

        if not update_queue:
            print("[update_knowledge_base] Queue is empty.")
            return

        filename, label, doc_type = update_queue.popleft()
        print(f"[update_knowledge_base] Processing '{filename}' → label='{label}'")

        if doc_type == "pdf":
            doc_path = LABEL_DIR_MAP.get(label, LABEL_DIR_MAP["Other"]) / "pdf" / filename
            content  = self.extract_text(str(doc_path))

            if not content:
                print(f"[update_knowledge_base] No text extracted from {filename}. Skipping.")
                return

            chunks     = _splitter.split_text(content)
            num_stored = self._ingest_chunks(chunks, label, filename)
            print(f"[update_knowledge_base] Stored {num_stored} chunks for '{filename}'.")

        else:
            print(f"[update_knowledge_base] Unsupported doc_type='{doc_type}'. Skipping.")


# =========================
# Manual test entry point
# =========================
if __name__ == "__main__":
    test_path = "D:\\Helio\\Helio\\Assets\\Image documents\\AADHAR demo.jpeg"
    processor = DocumentProcessor()
    text = processor.extract_text(test_path)
    print("Extracted text:", text)