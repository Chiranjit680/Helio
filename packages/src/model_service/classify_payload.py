import logging
from typing import List, TypedDict
from concurrent.futures import ThreadPoolExecutor
from fastapi import HTTPException, status

from model_store import get_or_load_classifier
import asyncio
from schema import ClassificationResult
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





def _validate_classification_inputs(
    text: str,
    candidate_labels: List[str],
) -> None:
    """Raise HTTP 422 if inputs are invalid."""
    if not text or not text.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Classification text is required.",
        )
    if not candidate_labels:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one candidate label is required.",
        )




def _run_classifier(text: str, candidate_labels: List[str]) -> ClassificationResult:
    """Run inference synchronously (call via executor to avoid blocking)."""
    classifier = get_or_load_classifier()
    logger.debug("Classifying text (first 50 chars): %.50s", text)

    result = classifier(sequences=text, candidate_labels=candidate_labels)
    return ClassificationResult(label=result["labels"][0], score=result["scores"][0])


async def _classify_payload(
    text: str,
    candidate_labels: List[str] = DEFAULT_LABELS,
) -> ClassificationResult:
    """Validate inputs and run zero-shot classification off the event loop."""
    _validate_classification_inputs(text, candidate_labels)

    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(
        _executor,
        _run_classifier,
        text,
        candidate_labels,
    )


if __name__ == "__main__":
    text = "The auth bug is causing login failures for users. We need to fix it ASAP."
    print(asyncio.run(_classify_payload(text, DEFAULT_LABELS)))

    