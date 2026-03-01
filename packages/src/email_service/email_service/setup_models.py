"""
Setup script to pre-download and cache ML models for Helio email classifier.
Run this once after installation to download models before first use.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from email_classifier import preload_model, list_cached_models, MODEL_CACHE_DIR


def setup_models():
    """Download and cache all required models."""
    print("="*70)
    print("Helio Email Classifier - Model Setup")
    print("="*70)
    print(f"\nCache Directory: {MODEL_CACHE_DIR}")
    print()
    
    # Check existing cache
    cached = list_cached_models()
    if cached:
        print(f"📦 Already cached models: {', '.join(cached)}\n")
    
    # Models to download
    models = [
        ("valhalla/distilbart-mnli-12-3", "~500 MB", "Recommended - Fast & accurate"),
        # Uncomment to also download the larger model
        # ("facebook/bart-large-mnli", "~1.6 GB", "More accurate but slower"),
    ]
    
    print("📥 Downloading models...\n")
    
    for model_id, size, description in models:
        print(f"Model: {model_id}")
        print(f"Size: {size}")
        print(f"Info: {description}")
        print("-" * 70)
        
        try:
            preload_model(model_id)
            print()
        except Exception as e:
            print(f"❌ Error downloading {model_id}: {e}\n")
            continue
    
    # Final summary
    print("="*70)
    cached_after = list_cached_models()
    print(f"\n✅ Setup complete! {len(cached_after)} model(s) cached:")
    for model in cached_after:
        print(f"   • {model}")
    
    print(f"\n💾 Total cache location: {MODEL_CACHE_DIR}")
    print("\nYou can now run email_classifier.py without downloads.")
    print("="*70)


if __name__ == "__main__":
    setup_models()
