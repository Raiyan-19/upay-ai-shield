"""
ai_models_and_chatbot - Gemini AI Forensic Investigation Assistant
Calls Google Gemini API with evidence grounding, strict role constraints,
and anti-hallucination safeguards for fraud analysts.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ai_models.gemini_assistant")

SYSTEM_INSTRUCTION = """You are an expert financial crime and transaction risk investigation AI assistant for mobile financial wallets (upay, bKash, Nagad).
Your role is to assist human compliance analysts in interpreting risk signals.

CRITICAL OPERATIONAL RULES:
1. Ground every claim strictly in the provided transaction evidence and risk score.
2. NEVER declare a transaction as 100% definitively fraudulent or innocent on your own authority. Frame findings as 'risk indicators', 'empirical anomalies', or 'suspicious deviations'.
3. NEVER make autonomous financial decisions or recommend immediate account freeze; all actions require human analyst verification.
4. Currency context: Express all monetary values in Bangladesh Taka (৳ / BDT).
5. Tone: Professional, analytical, concise, and structured. Use bullet points for key findings.
"""


try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass


class GeminiAssistant:
    """
    Connects to Google Gemini API for intelligent, contextual transaction investigations.
    Supports official google-genai SDK, legacy SDK, and direct REST API fallback.
    """

    def __init__(self, api_key: Optional[str] = None):
        try:
            from dotenv import load_dotenv
            load_dotenv()
        except Exception:
            pass

        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.client = None
        self.sdk_type = None
        self.active_model = None
        self.model_candidates = [
            "gemini-2.5-flash",
            "gemini-2.0-flash",
            "gemini-1.5-flash",
            "gemini-1.5-pro",
            "gemini-flash-latest"
        ]
        self._init_client()

    def _init_client(self):
        if not self.api_key:
            logger.info("No GEMINI_API_KEY provided. GeminiAssistant will be inactive.")
            return

        try:
            # Try new google-genai SDK
            from google import genai
            self.client = genai.Client(api_key=self.api_key)
            self.sdk_type = "genai"
            logger.info("Initialized google-genai client.")
        except ImportError:
            try:
                # Fallback to legacy google.generativeai SDK
                import google.generativeai as gai
                gai.configure(api_key=self.api_key)
                self.client = gai
                self.sdk_type = "legacy"
                logger.info("Initialized google.generativeai client.")
            except ImportError:
                # Direct REST fallback using requests/urllib
                self.client = "rest"
                self.sdk_type = "rest"
                logger.info("Using direct Gemini REST client.")

    def is_available(self) -> bool:
        return self.client is not None and bool(self.api_key)

    def _call_rest_api(self, prompt: str, model_name: str) -> str:
        """Direct HTTPS REST fallback for Gemini generation."""
        import requests
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
        headers = {"Content-Type": "application/json"}
        payload = {
            "system_instruction": {"parts": [{"text": SYSTEM_INSTRUCTION}]},
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.2}
        }
        res = requests.post(url, headers=headers, json=payload, timeout=25)
        if res.status_code == 200:
            data = res.json()
            candidates = data.get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    return parts[0].get("text", "").strip()
        raise RuntimeError(f"REST API failed with HTTP {res.status_code}: {res.text}")

    def generate_response(
        self,
        user_message: str,
        transaction_context: Optional[Dict[str, Any]] = None,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """
        Queries Gemini API with the transaction evidence and analyst inquiry.
        """
        if not self.is_available():
            raise RuntimeError("Gemini API client is not configured or GEMINI_API_KEY is missing.")

        prompt = self._construct_prompt(user_message, transaction_context, chat_history)

        for model_name in self.model_candidates:
            try:
                if self.sdk_type == "genai":
                    response = self.client.models.generate_content(
                        model=model_name,
                        contents=prompt,
                        config={"temperature": 0.2, "system_instruction": SYSTEM_INSTRUCTION}
                    )
                    self.active_model = model_name
                    return response.text.strip()
                elif self.sdk_type == "legacy":
                    model = self.client.GenerativeModel(
                        model_name=model_name,
                        system_instruction=SYSTEM_INSTRUCTION
                    )
                    response = model.generate_content(prompt)
                    self.active_model = model_name
                    return response.text.strip()
                elif self.sdk_type == "rest":
                    text = self._call_rest_api(prompt, model_name)
                    self.active_model = model_name
                    return text
            except Exception as e:
                logger.warning(f"Gemini model {model_name} failed: {e}. Trying next candidate...")
                continue

        # Try REST as final fallback even if SDK failed
        if self.sdk_type != "rest":
            try:
                text = self._call_rest_api(prompt, "gemini-1.5-flash")
                self.active_model = "gemini-1.5-flash"
                return text
            except Exception:
                pass

        raise RuntimeError("All Gemini candidate models failed to return a response.")

    def _construct_prompt(
        self,
        message: str,
        context: Optional[Dict[str, Any]],
        history: Optional[List[Dict[str, str]]]
    ) -> str:
        parts = []

        if context:
            parts.append("### TRANSACTION EVIDENCE CONTEXT:")
            parts.append("```json")
            parts.append(json.dumps(context, indent=2, default=str))
            parts.append("```\n")

        if history:
            parts.append("### RECENT CONVERSATION HISTORY:")
            for turn in history[-4:]:
                role = turn.get("role", "user").capitalize()
                text = turn.get("content", "")
                parts.append(f"{role}: {text}")
            parts.append("")

        parts.append(f"ANALYST INQUIRY: {message}")
        parts.append("\nPlease provide a structured, evidence-grounded investigation response.")

        return "\n".join(parts)
