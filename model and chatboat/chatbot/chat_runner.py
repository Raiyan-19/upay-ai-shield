"""
ai_models_and_chatbot - Unified Chatbot Runner
Seamlessly routes queries to Google Gemini API when available,
or falls back to the high-speed local forensic assistant.
"""

import os
import logging
from typing import Dict, Any, List, Optional
try:
    from .gemini_assistant import GeminiAssistant
    from .local_assistant import LocalChatAssistant
except ImportError:
    from gemini_assistant import GeminiAssistant
    from local_assistant import LocalChatAssistant

logger = logging.getLogger("ai_models.chat_runner")


class ChatAssistant:
    """
    Unified AI Forensic Chatbot for financial transaction risk investigation.
    """

    def __init__(self, gemini_api_key: Optional[str] = None):
        self.gemini = GeminiAssistant(api_key=gemini_api_key)
        self.local = LocalChatAssistant()

    def is_gemini_active(self) -> bool:
        return self.gemini.is_available()

    def get_status(self) -> Dict[str, Any]:
        return {
            "gemini_available": self.gemini.is_available(),
            "active_model": getattr(self.gemini, "active_model", None) or ("gemini-2.5-flash" if self.gemini.is_available() else "local-rules-engine"),
            "sdk_type": getattr(self.gemini, "sdk_type", None),
            "candidates": self.gemini.model_candidates
        }

    def chat(
        self,
        message: str,
        transaction_context: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None,
        history: Optional[List[Dict[str, str]]] = None,
        force_local: bool = False,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Processes analyst inquiry and returns structured answer.
        Supports dynamic Gemini API key or environment configuration.
        """
        eff_history = chat_history or history
        # Allow dynamic override of API key if passed
        active_gemini = self.gemini
        if api_key and (not self.gemini.is_available() or self.gemini.api_key != api_key):
            active_gemini = GeminiAssistant(api_key=api_key)

        if not force_local and active_gemini.is_available():
            try:
                answer = active_gemini.generate_response(
                    user_message=message,
                    transaction_context=transaction_context,
                    chat_history=eff_history
                )
                return {
                    "response": answer,
                    "engine_used": "gemini-api",
                    "model": getattr(active_gemini, "active_model", "gemini-2.0-flash"),
                    "status": "success"
                }
            except Exception as e:
                logger.warning(f"Gemini call failed ({e}); falling back to local intelligence assistant.")

        # Local intelligent fallback
        answer = self.local.generate_response(
            user_message=message,
            transaction_context=transaction_context
        )
        return {
            "response": answer,
            "engine_used": "local-intelligence-engine",
            "model": "local-forensic-engine",
            "status": "success"
        }


# Global singleton
_chat_instance = None

def get_chatbot(api_key: Optional[str] = None) -> ChatAssistant:
    global _chat_instance
    if _chat_instance is None or (api_key and _chat_instance.gemini.api_key != api_key):
        _chat_instance = ChatAssistant(gemini_api_key=api_key)
    return _chat_instance

def ask_chatbot(
    message: str,
    transaction_context: Optional[Dict[str, Any]] = None,
    api_key: Optional[str] = None
) -> Dict[str, Any]:
    """Convenience helper function."""
    bot = get_chatbot(api_key=api_key)
    return bot.chat(message=message, transaction_context=transaction_context, api_key=api_key)


if __name__ == "__main__":
    test_context = {
        "transaction_id": "TX109945",
        "amount": 42000.0,
        "amount_deviation": 8.5,
        "is_new_device": 1,
        "is_new_receiver": 1,
        "failed_attempts": 2,
        "hour": 2,
        "risk_score": 92.4,
        "risk_level": "HIGH"
    }

    bot = ChatAssistant()
    res = bot.chat("Is this transaction an Account Takeover?", transaction_context=test_context)
    print("Chatbot Response:\n", res["response"])
    print("\nEngine Used:", res["engine_used"])
