import os
import json
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from google import genai
from google.genai import types

# 1. Define the Output Schema (Matches your PostgreSQL DB)
class EmailAnalysisResult(BaseModel):
    category: str = Field(..., description="Category: 'Work', 'Personal', 'Promotional', 'Spam', 'Urgent'")
    importance_score: int = Field(..., description="Score from 1 (Low) to 5 (High)")
    urgency_score: int = Field(..., description="Score from 1 (Low) to 5 (High)")
    summary: str = Field(..., description="A concise 1-sentence summary of the email")
    intent: str = Field(..., description="The primary intent: 'Invoice', 'Meeting', 'FYI', 'Action Required'")

def email_agent(
    email_content: str,
    sender_info: str="",
    recent_context: str = "",
    model_id: str = "gemini-3-flash-preview", # Faster model for high volume
    api_key: Optional[str] = None
) -> dict:
    """
    Analyzes an email using Gemini to extract structured metadata for Helio.
    """
    
    # Ensure API key is available (allow passing directly or via .env)
    if api_key is None:
        api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")

    client = genai.Client(api_key=api_key)

    # 2. Construct the Prompt with Context
    prompt = f"""
    You are the Intelligence Layer for Helio, an autonomous business system.
    Analyze the following incoming email.
    
    CONTEXT (Last 5 emails from this sender):
    {recent_context}
    
    INCOMING EMAIL:
    From: {sender_info}
    Content: {email_content}
    
    INSTRUCTIONS:
    1. Categorize the email precisely.
    2. Rate Importance and Urgency (1-5) based on the sender history and content.
    3. If it is a Bill/Invoice, set intent to 'Invoice'.
    """

    # 3. Call Gemini with Structured Output Config
    try:
        response = client.models.generate_content(
            model=model_id,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=EmailAnalysisResult, # Enforce the Pydantic schema
                temperature=0.1 # Low temp for consistent, factual extraction
            )
        )
        
        # 4. Return as Python Dict (Ready for DB insert)
        # The SDK handles the JSON parsing automatically when schema is provided
        return response.parsed

    except Exception as e:
        print(f"Helio Intelligence Error: {e}")
        # Return a safe fallback so the pipeline doesn't crash
        return {
            "category": "Uncategorized", 
            "importance_score": 1, 
            "urgency_score": 1, 
            "summary": "Error in AI processing", 
            "intent": "Unknown"
        }

# --- Example Usage ---
if __name__ == "__main__":
    email_text = "Hey, just following up on the invoice #9921 I sent last week. We need payment by Friday."
    sender = "vendor@acme.com"
    context = "Previous email: Sent Invoice #9921 on Jan 20th. Subject: January Services."
    # Load environment from repo root .env so local runs pick up keys
    BASE_DIR = Path(__file__).resolve().parents[4]
    load_dotenv(dotenv_path=BASE_DIR / ".env")

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    result = email_agent(email_text, sender, context, api_key=api_key)
    print(type(result))
    print(result)
    # Output will be a strictly formatted object like:
    # {
    #   'category': 'Finance', 
    #   'importance_score': 5, 
    #   'urgency_score': 5, 
    #   'summary': 'Follow-up on unpaid invoice #9921 requiring payment by Friday.', 
    #   'intent': 'Invoice'
    # }