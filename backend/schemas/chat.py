from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: str = Field(..., description="user or assistant")
    content: str


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)
    context_type: Optional[str] = "general"  # general, transaction, case, policy
    context_id: Optional[str] = None
    transaction_id: Optional[str] = None
    context: Optional[Dict[str, Any]] = None
    history: Optional[List[ChatMessage]] = []
    api_key: Optional[str] = Field(None, description="Optional Google Gemini API key to activate Gemini AI")


class ChatResponse(BaseModel):
    reply: str
    intent: Optional[str] = "fraud_analysis"
    confidence: Optional[float] = 0.95
    suggested_actions: Optional[List[str]] = []
    related_entities: Optional[Dict[str, Any]] = None
