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