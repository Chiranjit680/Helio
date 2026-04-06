from pathlib import Path
from typing import Any, Dict

from transformers import pipeline


BASE_DIR = Path(__file__).resolve().parent
MODEL_CACHE_DIR = BASE_DIR / "models" / "huggingface_cache"
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# In-memory singleton cache for loaded model pipelines.
_classifier_cache: Dict[str, Any] = {}


def get_or_load_classifier(model_id: str = "valhalla/distilbart-mnli-12-3"):
    """Return a cached zero-shot classifier, loading it on first call."""
    if model_id in _classifier_cache:
        return _classifier_cache[model_id]

    classifier = pipeline(
        "zero-shot-classification",
        model=model_id,
        device=-1,
        model_kwargs={"cache_dir": str(MODEL_CACHE_DIR)},
    )
    _classifier_cache[model_id] = classifier
    return classifier

def preload_bart_model(model_id: str = "valhalla/distilbart-mnli-12-3") -> bool:
    """Pre-download and cache model at startup."""
    print(f"Pre-loading model: {model_id}")

    try:
        get_or_load_classifier(model_id)
        print(f"Model '{model_id}' downloaded/loaded and cached")
    except Exception as exc:
        print(f"Failed to preload model '{model_id}': {exc}")
        return False

    return True
