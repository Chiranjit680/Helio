# import redis
# import json
# import time
# import requests
# from pathlib import Path
# from model_service.generate_chunks import generate_chunks
# import chromadb


# BASE_DIR = Path(__file__).resolve().parent

# LABEL_DIR_MAP = {
#     "Software development and engineering":    BASE_DIR / "Engineering_docs",
#     "Human resources and employee management": BASE_DIR / "HR_docs",
#     "Finance and accounting":                  BASE_DIR / "Finance_docs",
#     "Legal and compliance":                    BASE_DIR / "Legal_docs",
#     "Marketing and branding":                  BASE_DIR / "Marketing_docs",
#     "Sales and business development":          BASE_DIR / "Sales_docs",
#     "Operations and logistics":                BASE_DIR / "Operations_docs",
#     "Other":                                   BASE_DIR / "Other_docs",
# }
# chroma_client_engineering = chromadb.PersistentClient(path=str(BASE_DIR / "Engineering_docs" / "chroma_store"))
# chroma_client_hr = chromadb.PersistentClient(path=str(BASE_DIR / "HR_docs" / "chroma_store"))
# chroma_client_finance = chromadb.PersistentClient(path=str(BASE_DIR / "Finance_docs" / "chroma_store"))
# chroma_client_legal = chromadb.PersistentClient(path=str(BASE_DIR / "Legal_docs" / "chroma_store"))  
# chroma_client_marketing = chromadb.PersistentClient(path=str(BASE_DIR / "Marketing_docs" / "chroma_store"))
# chroma_client_sales = chromadb.PersistentClient(path=str(BASE_DIR / "Sales_docs" / "chroma_store"))
# chroma_client_operations = chromadb.PersistentClient(path=str(BASE_DIR / "Operations_docs" / "chroma_store"))
# chroma_client_other = chromadb.PersistentClient(path=str(BASE_DIR / "Other_docs" / "chroma_store"))
# r = redis.Redis(host='localhost', port=6379, db=0)
# chroma_client1 = chroma_client_engineering

# def push_to_queue(task_data):
#     r.lpush("task_queue", json.dumps(task_data))


# def update_knowledge_base():
#     task = r.rpop("task_queue")

#     while task is not None:
#         task_data = json.loads(task)
#         file= task_data["filename"]
#         label = task_data["label"]
#         type = task_data["type"]
#         data= {
#             "doc_path": file
#         }
       
#         chunks, chunk_embeddings = generate_chunks(file)
#         if label == "Software development and engineering":
#             chroma_client1.get_or_create_collection(name="engineering").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Human resources and employee management":
#             chroma_client_hr.get_or_create_collection(name="hr").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Finance and accounting":
#             chroma_client_finance.get_or_create_collection(name="finance").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Legal and compliance":
#             chroma_client_legal.get_or_create_collection(name="legal").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Marketing and branding":
#             chroma_client_marketing.get_or_create_collection(name="marketing").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Sales and business development":
#             chroma_client_sales.get_or_create_collection(name="sales").add(
#                 documents=chunks,
#                 embeddings=dings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         elif label == "Operations and logistics":
#             chroma_client_operations.get_or_create_collection(name="operations").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
#         else:
#             chroma_client_other.get_or_create_collection(name="other").add(
#                 documents=chunks,
#                 embeddings=chunk_embeddings,
#                 ids=[f"{file}_{i}" for i in range(len(chunks))]
#             )
        
        


#         task = r.rpop("task_queue")
import redis
import json
import logging
from pathlib import Path
from model_service.generate_chunks import generate_chunks
import chromadb

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).resolve().parent

# Single source of truth: label → (chroma path, collection name)
LABEL_CONFIG = {
    "Software development and engineering":    ("Engineering_docs",  "engineering"),
    "Human resources and employee management": ("HR_docs",           "hr"),
    "Finance and accounting":                  ("Finance_docs",       "finance"),
    "Legal and compliance":                    ("Legal_docs",         "legal"),
    "Marketing and branding":                  ("Marketing_docs",     "marketing"),
    "Sales and business development":          ("Sales_docs",         "sales"),
    "Operations and logistics":                ("Operations_docs",    "operations"),
    "Other":                                   ("Other_docs",         "other"),
}

# Build clients once at startup
_chroma_clients = {
    label: chromadb.PersistentClient(path=str(BASE_DIR / dir_name / "chroma_store"))
    for label, (dir_name, _) in LABEL_CONFIG.items()
}

r = redis.Redis(host="localhost", port=6379, db=0)


def push_to_queue(task_data: dict) -> None:
    r.lpush("task_queue", json.dumps(task_data))


def _get_client_and_collection(label: str) -> tuple:
    """Return (chroma_client, collection_name) for a given label."""
    config = LABEL_CONFIG.get(label, LABEL_CONFIG["Other"])
    _, collection_name = config
    client = _chroma_clients.get(label, _chroma_clients["Other"])
    return client, collection_name


def update_knowledge_base() -> None:
    while True:
        raw = r.brpop("task_queue", timeout=5)  # blocking pop, 5s timeout
        if raw is None:
            break  # queue drained; exit (or `continue` to run forever)

        _, task_bytes = raw
        try:
            task_data = json.loads(task_bytes)
            file = task_data["filename"]
            label = task_data["label"]

            logger.info("Processing file=%s label=%s", file, label)

            chunks, chunk_embeddings = generate_chunks(file)

            client, collection_name = _get_client_and_collection(label)
            collection = client.get_or_create_collection(name=collection_name)
            collection.add(
                documents=chunks,
                embeddings=chunk_embeddings,
                ids=[f"{file}_{i}" for i in range(len(chunks))],
            )

            logger.info("Stored %d chunks for %s", len(chunks), file)

        except KeyError as e:
            logger.error("Malformed task (missing key %s): %s", e, task_bytes)
        except Exception as e:
            logger.exception("Failed to process task: %s", e)