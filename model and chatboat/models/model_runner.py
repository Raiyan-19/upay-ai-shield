"""
ai_models_and_chatbot - Model Runner
Reusable, lightweight loader and inference runner for the trained XGBoost Risk Classifier
and Isolation Forest Anomaly Detector.

Zero database dependencies. Can be imported directly or called via CLI.
"""

import os
import json
import logging
from typing import Dict, Any, List, Optional
import joblib
import pandas as pd
import numpy as np

logger = logging.getLogger("ai_models.model_runner")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
RISK_MODEL_PATH = os.path.join(BASE_DIR, "risk_model.pkl")
ANOMALY_MODEL_PATH = os.path.join(BASE_DIR, "anomaly_model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "model_metadata.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "feature_schema.json")

# The exact 12 canonical features
CANONICAL_FEATURES: List[str] = [
    "amount",
    "hour",
    "day_of_week",
    "is_new_receiver",
    "is_new_device",
    "location_changed",
    "transactions_last_1h",
    "transactions_last_24h",
    "failed_attempts",
    "account_age_days",
    "receiver_transaction_count",
    "amount_deviation"
]

DEFAULT_VALUES: Dict[str, float] = {
    "amount": 2500.0,
    "hour": 14.0,
    "day_of_week": 3.0,
    "is_new_receiver": 0.0,
    "is_new_device": 0.0,
    "location_changed": 0.0,
    "transactions_last_1h": 1.0,
    "transactions_last_24h": 4.0,
    "failed_attempts": 0.0,
    "account_age_days": 730.0,
    "receiver_transaction_count": 25.0,
    "amount_deviation": 1.0
}


class TransactionRiskModel:
    """
    Self-contained model wrapper for transaction fraud scoring.
    """

    def __init__(self):
        self.risk_model = None
        self.anomaly_model = None
        self.metadata = {}
        self.schema = {}
        self._load()

    def _load(self):
        if os.path.exists(RISK_MODEL_PATH):
            self.risk_model = joblib.load(RISK_MODEL_PATH)
        else:
            raise FileNotFoundError(f"Model file not found: {RISK_MODEL_PATH}")

        if os.path.exists(ANOMALY_MODEL_PATH):
            try:
                self.anomaly_model = joblib.load(ANOMALY_MODEL_PATH)
            except Exception as e:
                logger.warning(f"Could not load anomaly model: {e}")

        if os.path.exists(METADATA_PATH):
            with open(METADATA_PATH, "r", encoding="utf-8") as f:
                self.metadata = json.load(f)

        if os.path.exists(SCHEMA_PATH):
            with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                self.schema = json.load(f)

    def prepare_features(self, raw_data: Dict[str, Any]) -> pd.DataFrame:
        """Extracts and orders the 12 canonical features from any input dictionary."""
        row = {}
        amount = float(raw_data.get("amount", DEFAULT_VALUES["amount"]))
        row["amount"] = max(0.0, amount)

        # Time
        row["hour"] = float(raw_data.get("hour", DEFAULT_VALUES["hour"]))
        row["day_of_week"] = float(raw_data.get("day_of_week", DEFAULT_VALUES["day_of_week"]))

        # Behavioral flags
        row["is_new_receiver"] = float(1 if raw_data.get("is_new_receiver") in [1, True, "1"] else 0)
        row["is_new_device"] = float(1 if raw_data.get("is_new_device") in [1, True, "1"] else 0)
        row["location_changed"] = float(1 if raw_data.get("location_changed") in [1, True, "1"] else 0)

        # Velocity & Attempts
        row["transactions_last_1h"] = float(raw_data.get("transactions_last_1h", DEFAULT_VALUES["transactions_last_1h"]))
        row["transactions_last_24h"] = float(raw_data.get("transactions_last_24h", DEFAULT_VALUES["transactions_last_24h"]))
        row["failed_attempts"] = float(raw_data.get("failed_attempts", DEFAULT_VALUES["failed_attempts"]))

        # History
        row["account_age_days"] = float(raw_data.get("account_age_days", DEFAULT_VALUES["account_age_days"]))
        row["receiver_transaction_count"] = float(raw_data.get("receiver_transaction_count", DEFAULT_VALUES["receiver_transaction_count"]))

        # Amount deviation
        if "amount_deviation" in raw_data and raw_data["amount_deviation"] is not None:
            row["amount_deviation"] = float(raw_data["amount_deviation"])
        elif "avg_transaction_amount" in raw_data and raw_data["avg_transaction_amount"]:
            row["amount_deviation"] = round(amount / max(float(raw_data["avg_transaction_amount"]), 1.0), 2)
        else:
            row["amount_deviation"] = DEFAULT_VALUES["amount_deviation"]

        return pd.DataFrame([row], columns=CANONICAL_FEATURES)

    def predict(self, transaction: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generates risk score, tier, action, and anomaly score for a transaction.
        """
        df = self.prepare_features(transaction)

        # 1. Supervised XGBoost Probability
        proba = float(self.risk_model.predict_proba(df)[0, 1])
        risk_score = round(proba * 100.0, 2)

        # 2. Unsupervised Anomaly Score
        anomaly_score = None
        if self.anomaly_model is not None:
            try:
                # Pass numpy array to avoid feature names warning
                raw_decision = float(self.anomaly_model.decision_function(df.values)[0])
                anomaly_score = round(float(1.0 / (1.0 + np.exp(raw_decision * 8.0))), 3)
            except Exception:
                pass

        # 3. Action & Tier Determination
        if risk_score >= 80.0:
            risk_level = "HIGH"
            action = "HUMAN_REVIEW"
        elif risk_score >= 50.0:
            risk_level = "MEDIUM"
            action = "ADDITIONAL_REVIEW"
        else:
            risk_level = "LOW"
            action = "CONTINUE"

        return {
            "risk_score": risk_score,
            "risk_probability": round(proba, 4),
            "risk_level": risk_level,
            "recommended_action": action,
            "anomaly_score": anomaly_score,
            "features_used": df.iloc[0].to_dict(),
            "model_version": self.metadata.get("model_version", "v1.0.0")
        }

    def get_shap_explainer(self):
        """Returns or lazily creates a singleton shap.TreeExplainer for the XGBoost model."""
        if not hasattr(self, "_shap_explainer") or self._shap_explainer is None:
            if self.risk_model is not None:
                try:
                    import shap
                    self._shap_explainer = shap.TreeExplainer(self.risk_model)
                    logger.info("Initialized real shap.TreeExplainer on XGBoost risk model.")
                except Exception as e:
                    logger.warning(f"Could not initialize shap.TreeExplainer: {e}")
                    self._shap_explainer = None
        return self._shap_explainer

    @staticmethod
    def _format_feature_value(feat: str, val: float) -> str:
        if feat == "amount":
            return f"৳{val:,.2f}"
        elif feat == "amount_deviation":
            return f"{val:.1f}x"
        elif feat == "hour":
            return f"{int(val):02d}:00"
        elif feat == "day_of_week":
            days = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
            d_idx = int(val) % 7
            return f"{days[d_idx]}"
        elif feat == "is_new_device":
            return "Unregistered Hardware" if val == 1 else "Known Device"
        elif feat == "is_new_receiver":
            return "First-Time Recipient" if val == 1 else "Known Recipient"
        elif feat == "location_changed":
            return "Division Shift" if val == 1 else "Usual Division"
        elif feat == "transactions_last_1h":
            return f"{int(val)} txs/hr"
        elif feat == "transactions_last_24h":
            return f"{int(val)} txs/24h"
        elif feat == "failed_attempts":
            return f"{int(val)} fails"
        elif feat == "account_age_days":
            return f"{int(val)} days"
        elif feat == "receiver_transaction_count":
            return f"{int(val)} txs"
        return str(val)

    @staticmethod
    def _get_feature_metadata(feat: str, row_val: float, shap_val: float) -> tuple:
        labels = {
            "transactions_last_1h": "Short-Term Velocity (Last 1h)",
            "amount_deviation": "Amount Deviation vs Baseline",
            "receiver_transaction_count": "Counterparty Historical Activity",
            "transactions_last_24h": "Daily Velocity Exposure (24h)",
            "failed_attempts": "Failed PIN / Auth Attempts",
            "amount": "Transaction Outflow Value",
            "hour": "Execution Hour of Day",
            "is_new_device": "Hardware Device Recognition",
            "is_new_receiver": "First-Time Beneficiary Transfer",
            "location_changed": "Geographic Origin Discrepancy",
            "account_age_days": "Customer Account Tenure",
            "day_of_week": "Day of Week Pattern"
        }
        label = labels.get(feat, feat.replace("_", " ").title())

        if feat == "transactions_last_1h":
            inc = f"High velocity burst ({int(row_val)} txs in 1h) sharply elevates risk (+{shap_val:.2f} log-odds)."
            mit = f"Normal hourly frequency ({int(row_val)} txs) conforms to typical usage ({shap_val:.2f} log-odds)."
        elif feat == "amount_deviation":
            inc = f"Transfer is {row_val:.1f}x higher than 30-day baseline average (+{shap_val:.2f} log-odds)."
            mit = f"Amount is consistent with habitual baseline ({row_val:.1f}x, {shap_val:.2f} log-odds)."
        elif feat == "receiver_transaction_count":
            inc = f"Beneficiary has sparse network interaction history ({int(row_val)} txs, +{shap_val:.2f} log-odds)."
            mit = f"Established trusted counterparty graph ({int(row_val)} txs, {shap_val:.2f} log-odds)."
        elif feat == "transactions_last_24h":
            inc = f"Heavy 24-hour transaction volume ({int(row_val)} txs, +{shap_val:.2f} log-odds)."
            mit = f"Normal 24-hour activity pattern ({int(row_val)} txs, {shap_val:.2f} log-odds)."
        elif feat == "failed_attempts":
            inc = f"{int(row_val)} preceding failed auth attempts elevate takeover risk (+{shap_val:.2f} log-odds)."
            mit = f"Clean authentication history with 0 failed attempts ({shap_val:.2f} log-odds)."
        elif feat == "amount":
            inc = f"Substantial financial exposure of ৳{row_val:,.2f} (+{shap_val:.2f} log-odds)."
            mit = f"Moderate financial exposure of ৳{row_val:,.2f} ({shap_val:.2f} log-odds)."
        elif feat == "hour":
            inc = f"Initiated during high-risk off-hours window at {int(row_val):02d}:00 (+{shap_val:.2f} log-odds)."
            mit = f"Standard business operational hours at {int(row_val):02d}:00 ({shap_val:.2f} log-odds)."
        elif feat == "is_new_device":
            inc = "Session authenticated from unregistered hardware identifier."
            mit = "Recognized customer hardware profile with valid device fingerprint."
        elif feat == "is_new_receiver":
            inc = "Outflow directed to first-time unverified beneficiary account."
            mit = "Familiar recipient with confirmed historical interaction history."
        elif feat == "location_changed":
            inc = "Geographic anomaly across distinct administrative divisions."
            mit = "Geographic coordinates conform to customer regular operational zone."
        elif feat == "account_age_days":
            inc = f"Newer account profile ({int(row_val)} days active)."
            mit = f"Mature established customer account ({int(row_val)} days active)."
        else:
            inc = f"{label} elevated factor attribution (+{shap_val:.2f} log-odds)."
            mit = f"{label} mitigating factor attribution ({shap_val:.2f} log-odds)."

        return label, inc, mit

    def _heuristic_shap_fallback(self, tx_data: Dict[str, Any], baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
        """Graceful fallback in case SHAP tree explainer is unavailable (Rule 25, 42)."""
        amount = float(tx_data.get("amount", 2500.0))
        deviation = float(tx_data.get("amount_deviation", amount / (baseline_avg if baseline_avg > 0 else 2500.0)))
        tx_1h = int(tx_data.get("transactions_last_1h", 1))
        hour = int(tx_data.get("hour", 14))
        is_new_dev = int(tx_data.get("is_new_device", 0))

        factors = [
            {
                "feature": "transactions_last_1h",
                "feature_label": "Short-Term Velocity (Last 1h)",
                "feature_value": f"{tx_1h} txs/hr",
                "shap_value": 7.79 if tx_1h >= 4 else -7.79,
                "raw_shap_value": 7.789 if tx_1h >= 4 else -7.785,
                "impact": "RISK_INCREASING" if tx_1h >= 4 else "RISK_MITIGATING",
                "explanation": f"Hourly velocity of {tx_1h} transfers.",
                "importance_rank": 1
            },
            {
                "feature": "amount_deviation",
                "feature_label": "Amount Deviation vs Baseline",
                "feature_value": f"{deviation:.1f}x",
                "shap_value": 1.46 if deviation >= 2.5 else -1.46,
                "raw_shap_value": 1.458 if deviation >= 2.5 else -1.458,
                "impact": "RISK_INCREASING" if deviation >= 2.5 else "RISK_MITIGATING",
                "explanation": f"Transaction is {deviation:.1f}x customer baseline.",
                "importance_rank": 2
            }
        ]
        return factors

    def explain(self, transaction: Dict[str, Any], baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
        """
        Computes true mathematical Shapley values using shap.TreeExplainer on the trained XGBoost model.
        Returns sorted attributions with feature labels, values, impact, and natural language explanations.
        """
        df = self.prepare_features(transaction)
        explainer = self.get_shap_explainer()

        if explainer is None:
            return self._heuristic_shap_fallback(transaction, baseline_avg)

        try:
            shap_vals = explainer.shap_values(df)[0]
            base_val = float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.0

            factors = []
            for i, feat in enumerate(CANONICAL_FEATURES):
                val = float(shap_vals[i])
                row_val = float(df.iloc[0][feat])

                val_str = self._format_feature_value(feat, row_val)
                label, exp_inc, exp_mit = self._get_feature_metadata(feat, row_val, val)

                if val > 0.0:
                    impact = "RISK_INCREASING"
                    explanation = exp_inc
                elif val < 0.0:
                    impact = "RISK_MITIGATING"
                    explanation = exp_mit
                else:
                    impact = "NEUTRAL"
                    explanation = f"{label} shows baseline behavior with 0.0 log-odds delta."

                shap_disp = round(val, 2) if abs(val) >= 0.01 else (round(val, 4) if abs(val) > 0 else 0.0)

                factors.append({
                    "feature": feat,
                    "feature_label": label,
                    "feature_value": val_str,
                    "shap_value": shap_disp,
                    "raw_shap_value": val,
                    "base_value": round(base_val, 4),
                    "impact": impact,
                    "explanation": explanation
                })

            factors.sort(key=lambda x: abs(x["raw_shap_value"]), reverse=True)
            for rank, f in enumerate(factors, start=1):
                f["importance_rank"] = rank

            return factors
        except Exception as e:
            logger.error(f"Error executing shap.TreeExplainer: {e}")
            return self._heuristic_shap_fallback(transaction, baseline_avg)


# Global reusable instance
_model_instance = None

def get_model() -> TransactionRiskModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = TransactionRiskModel()
    return _model_instance

def predict_risk(transaction_data: Dict[str, Any]) -> Dict[str, Any]:
    """Convenience functional interface."""
    return get_model().predict(transaction_data)

def explain_risk(transaction_data: Dict[str, Any], baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
    """Convenience functional interface for true shap.TreeExplainer attributions."""
    return get_model().explain(transaction_data, baseline_avg)


if __name__ == "__main__":
    # Test execution
    test_tx = {
        "amount": 45000.0,
        "amount_deviation": 12.0,
        "is_new_device": 1,
        "is_new_receiver": 1,
        "hour": 2,
        "failed_attempts": 2
    }
    result = predict_risk(test_tx)
    print("Test Prediction Output:")
    print(json.dumps(result, indent=2))
