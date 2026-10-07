"""
ai_models_and_chatbot - Reusable AI Component Package
Contains:
1. Model Component: Trained XGBoost & Isolation Forest models + inference runner
2. Chatbot Component: Gemini AI & Local offline forensic investigation chatbot
3. Data Component: Sample transactions, customer baseline data, and loaders
"""

from .models.model_runner import (
    predict_risk,
    explain_risk,
    get_model,
    TransactionRiskModel,
    CANONICAL_FEATURES,
    predict_scam,
    get_scam_model,
    ScamNLPModel
)

from .chatbot.chat_runner import (
    ask_chatbot,
    get_chatbot,
    ChatAssistant
)

from .data.data_loader import (
    load_sample_transactions,
    load_sample_customers,
    get_transaction_by_id,
    get_customer_by_id
)

__version__ = "1.0.0"

__all__ = [
    "predict_risk",
    "explain_risk",
    "get_model",
    "TransactionRiskModel",
    "CANONICAL_FEATURES",
    "predict_scam",
    "get_scam_model",
    "ScamNLPModel",
    "ask_chatbot",
    "get_chatbot",
    "ChatAssistant",
    "load_sample_transactions",
    "load_sample_customers",
    "get_transaction_by_id",
    "get_customer_by_id"
]

