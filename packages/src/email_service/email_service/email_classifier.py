import os
import json
import re
from typing import Optional, Dict
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field

import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification
# Local model cache directory (stores downloaded models in project)
BASE_DIR = Path(__file__).resolve().parent
MODEL_CACHE_DIR = BASE_DIR / "models" / "huggingface_cache"
MODEL_CACHE_DIR.mkdir(parents=True, exist_ok=True)

# Global cache for loaded pipelines (singleton pattern)
_classifier_cache: Dict[str, any] = {}
_importance_model_cache: Dict[str, any] = {}  # Cache for importance prediction model


# 1. Define the Output Schema (Matches your PostgreSQL DB)
class EmailAnalysisResult(BaseModel):
    category: str = Field(..., description="Category: 'Work', 'Personal', 'Promotional', 'Spam', 'Urgent'")
   
    intent: str = Field(..., description="The primary intent: 'Invoice', 'Meeting', 'FYI', 'Action Required'")

def email_classifier(
    email_content: str,
    sender_info: str="",
    recent_context: str = "",
    model_id: str = "valhalla/distilbart-mnli-12-3",  # Can also use "valhalla/distilbart-mnli-12-3" for faster inference
    api_key: Optional[str] = None
) -> dict:
    """
    Analyzes an email using BART zero-shot classification to extract structured metadata for Helio.
    Models are cached locally in ./models/huggingface_cache/ for reuse.
    """
    
    # Check if classifier is already loaded (singleton pattern)
    if model_id in _classifier_cache:
        classifier = _classifier_cache[model_id]
    else:
        # Lazy import to avoid loading unnecessary modules at startup
        from transformers import pipeline
        
        # Check if model exists locally
        model_local_path = MODEL_CACHE_DIR / model_id.replace("/", "--")
        if model_local_path.exists():
            print(f"📂 Loading model from local cache: {model_local_path}")
        else:
            print(f"⬇️  Downloading model '{model_id}'... (this happens once)")
            print(f"   Caching to: {MODEL_CACHE_DIR}")
        
        # Initialize BART classifier with local cache
        classifier = pipeline(
            "zero-shot-classification",
            model=model_id,
            device=-1,  # Use CPU, change to 0 for GPU
            model_kwargs={"cache_dir": str(MODEL_CACHE_DIR)}
        )
        
        # Cache the pipeline for reuse
        _classifier_cache[model_id] = classifier
        print(f"✅ Model '{model_id}' loaded and cached in memory")
    
    # Define categories for classification
    categories = ["Work", "Personal", "Promotional", "Spam", "Urgent"]
    intents = ["Invoice", "Meeting", "FYI", "Action Required"]
    
    # Combine email content with sender for better context
    full_context = f"From: {sender_info}\n{email_content}"
    
    try:
        # 1. Classify Category
        print("🔄 Starting category classification...")
        category_result = classifier(
            full_context,
            candidate_labels=categories,
            multi_label=False
        )
        predicted_category = category_result['labels'][0]
        print(f"✓ Category: {predicted_category}")
        
        # 2. Classify Intent
        print("🔄 Starting intent classification...")
        intent_result = classifier(
            full_context,
            candidate_labels=intents,
            multi_label=False
        )
        predicted_intent = intent_result['labels'][0]
        print(f"✓ Intent: {predicted_intent}")
   
       
        
        # Return structured result
        return {
            "category": predicted_category,
           
            "intent": predicted_intent
        }

    except Exception as e:
        print(f"Helio Intelligence Error: {e}")
        # Return a safe fallback so the pipeline doesn't crash
        return {
            "category": "Uncategorized", 
            
            "intent": "Unknown"
        }


def _generate_summary(content: str, max_length: int = 100) -> str:
    """Generate a concise summary from email content."""
    # Clean content
    content = content.strip()
    
    # Try to get first sentence
    sentences = re.split(r'[.!?]+', content)
    if sentences and len(sentences[0].strip()) > 10:
        first_sentence = sentences[0].strip()
        if len(first_sentence) <= max_length:
            return first_sentence + "."
        else:
            # Truncate and add ellipsis
            return first_sentence[:max_length-3].strip() + "..."
    
    # Fallback: just truncate
    if len(content) <= max_length:
        return content
    else:
        return content[:max_length-3].strip() + "..."


def list_cached_models() -> list:
    """List all models currently cached locally."""
    if not MODEL_CACHE_DIR.exists():
        return []
    
    cached = []
    for item in MODEL_CACHE_DIR.iterdir():
        if item.is_dir():
            cached.append(item.name.replace("--", "/"))
    return cached


def preload_model(model_id: str = "valhalla/distilbart-mnli-12-3"):
    """
    Pre-download and cache a model without running classification.
    Useful for setup/initialization.
    """
    from transformers import pipeline
    
    print(f"📥 Pre-loading model: {model_id}")
    
    if model_id not in _classifier_cache:
        classifier = pipeline(
            "zero-shot-classification",
            model=model_id,
            device=-1,
            model_kwargs={"cache_dir": str(MODEL_CACHE_DIR)}
        )
        _classifier_cache[model_id] = classifier
        print(f"✅ Model '{model_id}' downloaded and cached")
    else:
        print(f"✅ Model '{model_id}' already loaded")
    
    return True


def predict_importance(text, model_path=None):
    # Use relative path if not specified
    if model_path is None:
        model_path = BASE_DIR / "iu_model"
    
    model_path_str = str(model_path)
    
    # Check if model is already cached
    if model_path_str in _importance_model_cache:
        tokenizer = _importance_model_cache[model_path_str]['tokenizer']
        model = _importance_model_cache[model_path_str]['model']
    else:
        # 1. Load the saved model and tokenizer
        tokenizer = AutoTokenizer.from_pretrained(model_path)
        model = AutoModelForSequenceClassification.from_pretrained(model_path)
        
        # Switch to evaluation mode (turns off dropout)
        model.eval()
        
        # Cache the model and tokenizer
        _importance_model_cache[model_path_str] = {
            'tokenizer': tokenizer,
            'model': model
        }
        print(f"✅ Importance model loaded and cached from: {model_path}")
    
    # 2. Tokenize the input text
    inputs = tokenizer(
        text, 
        return_tensors="pt", 
        truncation=True, 
        padding=True, 
        max_length=512
    )
    
    # Remove token_type_ids if present (DistilBERT doesn't use them)
    if 'token_type_ids' in inputs:
        inputs.pop('token_type_ids')
    
    # 3. Perform the forward pass
    with torch.no_grad():
        outputs = model(**inputs)
    
    # 4. Extract the score
    # .item() converts the 1x1 tensor to a standard Python float
    raw_score = outputs.logits.item()
    
    # 5. Post-processing: ensure it stays within 1-10 range
    final_score = max(1, min(10, raw_score))
    
    return round(final_score, 2)

def email_model_results(
    email_content: str,
    sender_info: str="",
    recent_context: str = "",
    model_id: str = "valhalla/distilbart-mnli-12-3",
    importance_model_path: Optional[str] = None
) -> dict:
    """
    Combines category/intent classification with importance prediction.
    """
    classification_result = email_classifier(
        email_content=email_content,
        sender_info=sender_info,
        recent_context=recent_context,
        model_id=model_id
    )
    
    importance_score = predict_importance(email_content, model_path=importance_model_path)
    
    classification_result['importance_score'] = importance_score
    
    return classification_result


# --- Example Usage ---
if __name__ == "__main__":
    print("="*60)
    print("Helio Email Classifier - BART Zero-Shot Classification")
    print(f"Model Cache Directory: {MODEL_CACHE_DIR}")
    print("="*60)
    
    # Test cases
    test_emails = [
        {
            "content": "Hey, just following up on the invoice #9921 I sent last week. We need payment by Friday.",
            "sender": "vendor@acme.com",
            "context": "Previous email: Sent Invoice #9921 on Jan 20th."
        },
        {
            "content": "URGENT: Server is down! Production environment is not responding. Need immediate attention!",
            "sender": "devops@company.com",
            "context": ""
        },
        {
            "content": "Hi! Check out our amazing deals on shoes! 50% off this weekend only. Shop now!",
            "sender": "marketing@shoesale.com",
            "context": ""
        }
    ]
    
    # Use smaller/faster model for demo: "valhalla/distilbart-mnli-12-3"
    # Or use full model: "facebook/bart-large-mnli"
    model = "valhalla/distilbart-mnli-12-3"  # Faster, smaller model
    
    # Show cached models
    cached_models = list_cached_models()
    if cached_models:
        print(f"\n📦 Cached models found: {', '.join(cached_models)}")
    else:
        print(f"\n📦 No cached models yet")
    print()
    
    for i, email in enumerate(test_emails, 1):
        print(f"\n{'='*60}")
        print(f"Test Email {i}")
        print(f"{'='*60}")
        print(f"From: {email['sender']}")
        print(f"Content: {email['content'][:80]}...")
        
        result = email_classifier(
            email_content=email['content'], 
            sender_info=email['sender'], 
            recent_context=email['context'],
            model_id=model
        )
        
        
        print(f"\n📊 Classification Result:")
        print(json.dumps(result, indent=2))
        
        try:
            result2= predict_importance(email['content'])
            print(f"\n📈 Importance/Urgency Score: {result2}/10")
        except Exception as e:
            print(f"\n⚠️  Importance prediction failed: {e}")
    
    print(f"\n{'='*60}")
    print("✅ All tests completed!")
    # Expected output format:
    # {
    #   "category": "Work",
    #   "summary": "Follow-up on unpaid invoice #9921 requiring payment by Friday.", 
    #   "intent": "Invoice"
    # }
    