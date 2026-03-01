# Model Cache Directory

This directory stores downloaded Hugging Face models locally to avoid re-downloading them.

## How It Works

1. **First Run**: Models are downloaded from Hugging Face Hub and cached here
2. **Subsequent Runs**: Models are loaded from this local cache (fast!)
3. **Storage**: Models are stored in `huggingface_cache/` subdirectory

## Cached Models

Models are automatically downloaded when first used in `email_classifier.py`:

- **`valhalla/distilbart-mnli-12-3`** (~500 MB) - Faster, lighter model
- **`facebook/bart-large-mnli`** (~1.6 GB) - More accurate, larger model

## Pre-loading Models

You can pre-download models without running classification:

```python
from email_classifier import preload_model

# Download and cache the model
preload_model("valhalla/distilbart-mnli-12-3")
```

## Listing Cached Models

```python
from email_classifier import list_cached_models

cached = list_cached_models()
print(f"Cached models: {cached}")
```

## Cache Location

Models are stored at:
```
packages/src/email_service/email_service/models/huggingface_cache/
```

## Git Ignore

The `huggingface_cache/` directory is ignored by git (see `.gitignore`) since:
- Model files are large (100s of MBs to GBs)
- They can be re-downloaded automatically
- Each developer can maintain their own cache

## Clearing Cache

To clear cached models and free up disk space:

```bash
# Remove all cached models
rm -rf huggingface_cache/

# Or on Windows
rmdir /s huggingface_cache
```

The models will be re-downloaded on next use.
