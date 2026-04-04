from pydantic import BaseModel, Field
from typing import List

class DocClassificationRequest(BaseModel):
    text: str = Field(..., description="The text to classify")
class DocClassificationResponse(BaseModel):
    label: str = Field(..., description="The predicted label for the document")
    score: float = Field(..., description="The confidence score for the prediction")
class GeminiQuery(BaseModel):
    text: str = Field(..., description="The text to classify for Gemini interface")