import logging
import asyncio
import os
from typing import List
from concurrent.futures import ThreadPoolExecutor

import numpy as np
from fastapi import HTTPException, status
from sklearn.metrics.pairwise import cosine_similarity
from sentence_transformers import SentenceTransformer

from schema import ClassificationResult
from sample_text import sample_text

logger = logging.getLogger(__name__)

DEFAULT_LABELS: List[str] = [
    "Finance and accounting",
    "Software development and engineering",
    "Human resources and employee management",
    "Sales and business development",
    "Marketing and branding",
    "Operations and logistics",
    "Legal and compliance",
    "Other",
]

_executor = ThreadPoolExecutor()
MODEL_PATH = r"models\huggingface_cache\all-MiniLM-L6-v2"

_model: SentenceTransformer | None = None


def get_embedding_model() -> SentenceTransformer:
    """Return a cached SentenceTransformer, loading it on first call."""
    global _model
    if _model is not None:
        return _model

    if os.path.exists(MODEL_PATH):
        logger.info("Loading model from local path: %s", MODEL_PATH)
        _model = SentenceTransformer(MODEL_PATH)
    else:
        logger.info("Local model not found, downloading all-MiniLM-L6-v2")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        _model.save(MODEL_PATH)

    return _model


def _run_semantic_classifier(text: str) -> ClassificationResult:
    """Blocking inference — must be called via executor."""
    model = get_embedding_model()

    text_embedding = model.encode(text).reshape(1, -1)  # shape (1, D)

    similarity_scores: dict[str, float] = {}
    for label, samples in sample_text.items():
        flattened_samples = [sample[0] if isinstance(sample, list) and sample else sample for sample in samples]
        sample_embeddings = model.encode(flattened_samples)           # shape (N, D)
        scores = cosine_similarity(text_embedding, sample_embeddings)  # (1, N)
        similarity_scores[label] = float(scores.mean())

    best_label = max(similarity_scores, key=similarity_scores.get)
    return ClassificationResult(label=best_label, score=similarity_scores[best_label])


async def classify_payload_semantic(text: str) -> ClassificationResult:
    """Validate input and run semantic classification off the event loop."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Classification text is required.",
        )

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(_executor, _run_semantic_classifier, text)


if __name__ == "__main__":
    text = "The auth bug is causing login failures for users. We need to fix it ASAP."
    result = asyncio.run(classify_payload_semantic(text))
    print(f"Label : {result.label}")
    print(f"Score : {result.score:.4f}")