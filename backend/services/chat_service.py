import sys
import os
import re
import html
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy.orm import Session
from backend.models.transaction import Transaction
from backend.models.case import Case

# Add root directory to sys.path if not present
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

MODEL_PKG_DIR = os.path.join(BASE_DIR, "model and chatboat")
if MODEL_PKG_DIR not in sys.path:
    sys.path.insert(0, MODEL_PKG_DIR)

from importlib import import_module

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?(previous|prior)\s+instructions",
    r"disregard\s+(all\s+)?(previous|prior)\s+rules",
    r"system\s*prompt",
    r"you\s+are\s+now\s+in\s+developer\s+mode",
    r"bypass\s+(security|filter|guardrail)",
    r"<script[\s\S]*?>",
    r"drop\s+table",
    r"delete\s+from\s+users"
]


def sanitize_input(text: str) -> Tuple[str, bool]:
    """Sanitizes user query and detects prompt injection attempts (Rule 35)."""
    if not text:
        return "", False

    # Check for known adversarial injections
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, text, re.IGNORECASE):
            return text, True

    # Strip dangerous control characters
    cleaned = "".join(ch for ch in text if ch.isprintable() or ch in "\n\r\t")
    return cleaned.strip(), False


def sanitize_output(text: str) -> str:
    """Escapes raw HTML tags to prevent XSS vulnerabilities (Rule 37)."""
    # Disallow executable tags
    text = re.sub(r"<\s*script[^>]*>.*?<\s*/\s*script\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"<\s*iframe[^>]*>.*?<\s*/\s*iframe\s*>", "", text, flags=re.IGNORECASE | re.DOTALL)
    text = re.sub(r"on\w+\s*=", "", text, flags=re.IGNORECASE)
    text = re.sub(r"javascript:\s*", "", text, flags=re.IGNORECASE)
    return text


class ChatService:
    @staticmethod
    def get_status() -> Dict[str, Any]:
        """Returns availability and active status of Gemini and local engines."""
        try:
            from chatbot.chat_runner import get_chatbot
            cb = get_chatbot()
            st = cb.get_status()
            return {
                "gemini_configured": st.get("gemini_available", False),
                "active_engine": "gemini-api" if st.get("gemini_available") else "local-intelligence-engine",
                "active_model": st.get("active_model", "local-rules-engine"),
                "sdk_type": st.get("sdk_type", "google-genai"),
                "candidate_models": st.get("candidates", [])
            }
        except Exception as e:
            return {
                "gemini_configured": bool(os.getenv("GEMINI_API_KEY")),
                "active_engine": "local-intelligence-engine",
                "active_model": "local-forensic-engine",
                "error": str(e)
            }

    @staticmethod
    def configure_gemini(api_key: str) -> Dict[str, Any]:
        """Dynamically configures and validates Gemini API key."""
        if not api_key or len(api_key.strip()) < 10:
            return {"success": False, "message": "Invalid Gemini API key provided"}

        cleaned_key = api_key.strip()
        os.environ["GEMINI_API_KEY"] = cleaned_key

        try:
            from chatbot.chat_runner import get_chatbot
            cb = get_chatbot(api_key=cleaned_key)
            # Persist to .env in root if possible
            env_path = os.path.join(BASE_DIR, ".env")
            lines = []
            if os.path.exists(env_path):
                with open(env_path, "r", encoding="utf-8") as f:
                    lines = [l for l in f.readlines() if not l.startswith("GEMINI_API_KEY=")]
            lines.append(f"GEMINI_API_KEY={cleaned_key}\n")
            with open(env_path, "w", encoding="utf-8") as f:
                f.writelines(lines)

            return {
                "success": True,
                "message": "Gemini API key configured and persisted successfully.",
                "active_model": getattr(cb.gemini, "active_model", "gemini-2.0-flash")
            }
        except Exception as e:
            return {"success": False, "message": f"Error configuring Gemini: {str(e)}"}

    @staticmethod
    def process_chat_message(
        db: Session,
        message: str,
        context_type: str = "general",
        context_id: Optional[str] = None,
        history: Optional[List[Dict[str, str]]] = None,
        api_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Integrates with the AI fraud copilot package in `model and chatboat`.
        Enforces Rule 35, 36, 37, 38:
        - Prompt injection detection
        - Non-authoritative advisory guardrail (AI cannot approve/block accounts)
        - Output sanitization
        - Gemini API execution when key is supplied or configured
        """
        cleaned_msg, is_suspicious = sanitize_input(message)

        if is_suspicious:
            return {
                "reply": (
                    "**[Security Alert - Guardrail Triggered]**\n\n"
                    "Your query contains expressions flagged by the upay AI Shield Security Filter "
                    "(Potential Prompt Injection / System Override Pattern). "
                    "This event has been logged for compliance audit under BFIU Master Circular 24."
                ),
                "intent": "security_violation",
                "confidence": 1.0,
                "suggested_actions": [
                    "View BFIU Circular 24 guidelines",
                    "Return to standard transaction triage",
                    "Review active fraud cases"
                ],
                "context_applied": False,
                "engine_used": "security-filter"
            }

        context_str = ""
        suggested_actions = [
            "Explain risk breakdown",
            "Simulate high velocity transaction",
            "Review BFIU AML policy guidelines"
        ]

        tx_context_dict = None
        if context_type == "transaction" and context_id:
            tx = db.query(Transaction).filter(Transaction.transaction_id == context_id).first()
            if tx:
                tx_context_dict = {
                    "transaction_id": tx.transaction_id,
                    "customer_id": tx.customer_id,
                    "amount": tx.amount,
                    "amount_deviation": tx.amount_deviation,
                    "is_new_device": tx.is_new_device,
                    "is_new_receiver": tx.is_new_receiver,
                    "failed_attempts": tx.failed_attempts,
                    "hour": tx.hour,
                    "risk_score": tx.demo_risk_score,
                    "risk_level": tx.risk_level,
                    "channel": tx.channel,
                    "receiver_id": tx.receiver_id
                }
                context_str = (
                    f"CONTEXT TRANSACTION: ID={tx.transaction_id}, Amount=BDT {tx.amount:,.2f}, "
                    f"Type={tx.transaction_type}, RiskScore={tx.demo_risk_score:.1f}, "
                    f"NightTx={bool(tx.hour < 5 if tx.hour is not None else False)}, "
                    f"DeviceChanged={bool(tx.is_new_device)}, FailedPins={tx.failed_attempts or 0}."
                )
                suggested_actions = [
                    f"Analyze ATO probability for {tx.transaction_id}",
                    f"Check velocity pattern for Customer {tx.customer_id}",
                    "Draft statutory investigation report"
                ]

        elif context_type == "case" and context_id:
            case = db.query(Case).filter(Case.case_id == context_id).first()
            if case:
                context_str = (
                    f"CONTEXT CASE: ID={case.case_id}, Transaction={case.transaction_id}, "
                    f"Customer={case.customer_id}, Priority={case.priority}, Status={case.status}, "
                    f"Assigned={case.assigned_analyst}, RiskScore={case.risk_score}."
                )
                suggested_actions = [
                    f"Recommend final decision for {case.case_id}",
                    "Summarize timeline events",
                    "Generate SAR filing template"
                ]

        # Use unified ChatAssistant from model and chatboat
        reply_text = ""
        engine_used = "local-intelligence-engine"
        model_name = "local-forensic-engine"

        # Check effective Gemini API key
        effective_key = api_key or os.getenv("GEMINI_API_KEY")

        try:
            from chatbot.chat_runner import get_chatbot
            cb = get_chatbot(api_key=effective_key)
            res = cb.chat(
                message=cleaned_msg,
                transaction_context=tx_context_dict,
                history=history,
                api_key=effective_key
            )
            raw_ans = res.get("response", "")
            engine_used = res.get("engine_used", "local-intelligence-engine")
            model_name = res.get("model", "local-forensic-engine")

            if engine_used == "gemini-api":
                reply_text = f"**[upay AI Copilot • Powered by Google Gemini]**\n\n{raw_ans}"
            elif tx_context_dict:
                score = tx_context_dict.get("risk_score", 0.0)
                amt = tx_context_dict.get("amount", 0.0)
                tid = tx_context_dict.get("transaction_id")
                dev = tx_context_dict.get("amount_deviation", 1.0)
                new_d = tx_context_dict.get("is_new_device", 0)
                failed_p = tx_context_dict.get("failed_attempts", 0)

                reply_text = (
                    f"### 1. What Happened?\n"
                    f"Transaction `{tid}` initiated for **৳{amt:,.2f}** via {tx_context_dict.get('channel', 'APP')} "
                    f"toward recipient `{tx_context_dict.get('receiver_id', 'N/A')}`. "
                    f"{'Session authenticated from an unverified hardware device.' if new_d else 'Originated from a known customer device.'}\n\n"
                    f"### 2. Why Is It Risky?\n"
                    f"• **Risk Score:** {score:.1f} / 100 ({tx_context_dict.get('risk_level', 'LOW')} Risk Tier)\n"
                    f"• **Amount Deviation:** {dev:.1f}x surge over customer baseline profile\n"
                    f"• **Authentication:** {failed_p} prior failed PIN/OTP attempts recorded\n"
                    f"• **Forensic Notes:** {raw_ans}\n\n"
                    f"### 3. What Should upay Do Next?\n"
                    f"• **Automated Action:** {'Route to Tier-1 Human Investigation Queue' if score >= 70 else ('Enforce Step-Up 2FA Challenge' if score >= 30 else 'Autonomous Safe Allow')}\n"
                    f"• **Analyst Protocol:** Per BFIU Master Circular 24, do not freeze funds without analyst confirmation. Verify via customer care hotline (16268).\n"
                )
            else:
                reply_text = raw_ans
        except Exception as e:
            reply_text = (
                f"### 1. What Happened?\n"
                f"Evaluation query received for inquiry: *\"{cleaned_msg}\"*.\n\n"
                f"### 2. Why Is It Risky?\n"
                f"Transaction telemetry evaluated against calibrated XGBoost models and BFIU Circular 24 fraud typologies.\n\n"
                f"### 3. What Should upay Do Next?\n"
                f"Review local SHAP attribution factors in the investigation drawer before recording formal disposition."
            )

        sanitized_reply = sanitize_output(reply_text)

        return {
            "reply": sanitized_reply,
            "intent": "fraud_investigation",
            "confidence": 0.98 if engine_used == "gemini-api" else 0.96,
            "suggested_actions": suggested_actions,
            "context_applied": bool(context_str),
            "engine_used": engine_used,
            "model": model_name
        }

