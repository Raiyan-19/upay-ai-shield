from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from fastapi.responses import JSONResponse
from backend.models.base import get_db
from backend.schemas.chat import ChatRequest
from backend.services.chat_service import ChatService

router = APIRouter(prefix="/api/v1/chat", tags=["AI Copilot"])


from pydantic import BaseModel
from typing import Optional


class ConfigureGeminiRequest(BaseModel):
    api_key: str


@router.get("/status")
def get_copilot_status():
    """Returns whether Gemini API is active, candidate models, and fallback status."""
    status = ChatService.get_status()
    return JSONResponse(content={"success": True, "data": status, **status})


@router.post("/configure")
def configure_gemini_key(req: ConfigureGeminiRequest):
    """Configures and activates Google Gemini API key at runtime."""
    res = ChatService.configure_gemini(req.api_key)
    return JSONResponse(status_code=200 if res.get("success") else 400, content=res)


@router.post("")
@router.post("/ask")
def ask_ai_copilot(req: ChatRequest, db: Session = Depends(get_db)):
    target_id = req.context_id or req.transaction_id
    context_type = req.context_type or ("transaction" if req.transaction_id else "general")

    result = ChatService.process_chat_message(
        db=db,
        message=req.message,
        context_type=context_type,
        context_id=target_id,
        history=[m.dict() for m in req.history] if req.history else [],
        api_key=req.api_key
    )

    data_payload = {
        "reply": result["reply"],
        "intent": result.get("intent", "fraud_investigation"),
        "confidence": result.get("confidence", 0.95),
        "suggested_actions": result.get("suggested_actions", []),
        "engine_used": result.get("engine_used", "local-intelligence-engine"),
        "model": result.get("model", "local-forensic-engine")
    }

    return JSONResponse(
        content={
            "success": True,
            "message": "AI copilot generated forensic reply",
            "reply": result["reply"],
            "intent": data_payload["intent"],
            "confidence": data_payload["confidence"],
            "suggested_actions": data_payload["suggested_actions"],
            "engine_used": data_payload["engine_used"],
            "model": data_payload["model"],
            "data": data_payload
        }
    )

