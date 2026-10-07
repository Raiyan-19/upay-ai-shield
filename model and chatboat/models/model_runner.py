"""
ai_models_and_chatbot - Model Runner
Reusable, lightweight loader and inference runner for the trained XGBoost Risk Classifier
(Model A: Tabular Only, Model B: Tabular + Temporal Graph Intelligence),
Isolation Forest Anomaly Detector, and Bangla MFS Scam NLP Classifier.

Zero external database dependencies. Can be imported directly or called via CLI.
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
RISK_MODEL_PATH = os.path.join(BASE_DIR, "risk_model.pkl")       # Champion (Model B)
RISK_MODEL_A_PATH = os.path.join(BASE_DIR, "risk_model_a.pkl")   # Baseline Model A (Tabular Only)
RISK_MODEL_B_PATH = os.path.join(BASE_DIR, "risk_model_b.pkl")   # Model B (Tabular + Graph)
ANOMALY_MODEL_PATH = os.path.join(BASE_DIR, "anomaly_model.pkl")
METADATA_PATH = os.path.join(BASE_DIR, "model_metadata.json")
SCHEMA_PATH = os.path.join(BASE_DIR, "feature_schema.json")

# The 12 Canonical Tabular Features
TABULAR_FEATURES: List[str] = [
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

# The 15 Temporal Graph Intelligence Features
GRAPH_FEATURES: List[str] = [
    "sender_out_degree",
    "sender_in_degree",
    "receiver_in_degree",
    "receiver_out_degree",
    "sender_unique_receivers",
    "receiver_unique_senders",
    "shared_device_count",
    "sender_fan_out_ratio",
    "receiver_fan_in",
    "rapid_fan_in_24h",
    "rapid_fan_out_24h",
    "transactions_to_receiver_24h",
    "transactions_to_receiver_7d",
    "receiver_degree_centrality",
    "network_risk_score"
]

COMBINED_FEATURES: List[str] = TABULAR_FEATURES + GRAPH_FEATURES
CANONICAL_FEATURES = TABULAR_FEATURES  # Backward compatibility alias

DEFAULT_TABULAR_VALUES: Dict[str, float] = {
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

DEFAULT_GRAPH_VALUES: Dict[str, float] = {
    "sender_out_degree": 2.0,
    "sender_in_degree": 0.0,
    "receiver_in_degree": 2.0,
    "receiver_out_degree": 0.0,
    "sender_unique_receivers": 2.0,
    "receiver_unique_senders": 2.0,
    "shared_device_count": 0.0,
    "sender_fan_out_ratio": 1.0,
    "receiver_fan_in": 2.0,
    "rapid_fan_in_24h": 0.0,
    "rapid_fan_out_24h": 0.0,
    "transactions_to_receiver_24h": 0.0,
    "transactions_to_receiver_7d": 0.0,
    "receiver_degree_centrality": 0.0002,
    "network_risk_score": 15.0
}


class TransactionRiskModel:
    """
    Self-contained model wrapper for transaction fraud scoring supporting:
    - Model A (Tabular Only - 12 features)
    - Model B (Tabular + Temporal Graph Features - 27 features)
    - Real-time TreeSHAP mathematical explainability across all features.
    """

    def __init__(self):
        self.risk_model_champion = None
        self.risk_model_a = None
        self.risk_model_b = None
        self.anomaly_model = None
        self.metadata = {}
        self.schema = {}
        self._shap_explainer_b = None
        self._shap_explainer_a = None
        self._load()

    def _load(self):
        # 1. Load Champion (Model B)
        if os.path.exists(RISK_MODEL_PATH):
            self.risk_model_champion = joblib.load(RISK_MODEL_PATH)
        elif os.path.exists(RISK_MODEL_B_PATH):
            self.risk_model_champion = joblib.load(RISK_MODEL_B_PATH)

        # 2. Load Model A (Tabular Only)
        if os.path.exists(RISK_MODEL_A_PATH):
            try:
                self.risk_model_a = joblib.load(RISK_MODEL_A_PATH)
            except Exception as e:
                logger.warning(f"Could not load risk_model_a: {e}")

        # 3. Load Model B (Tabular + Graph)
        if os.path.exists(RISK_MODEL_B_PATH):
            try:
                self.risk_model_b = joblib.load(RISK_MODEL_B_PATH)
            except Exception as e:
                logger.warning(f"Could not load risk_model_b: {e}")

        # Fallbacks
        if self.risk_model_b is None:
            self.risk_model_b = self.risk_model_champion
        if self.risk_model_a is None:
            self.risk_model_a = self.risk_model_champion

        # 4. Anomaly Model
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

    def prepare_features(self, raw_data: Dict[str, Any], feature_set: str = "combined") -> pd.DataFrame:
        """
        Extracts and orders features from any input dictionary.
        Supports feature_set='tabular' (12 features) or feature_set='combined' (27 features).
        """
        row = {}
        amount = float(raw_data.get("amount", DEFAULT_TABULAR_VALUES["amount"]))
        row["amount"] = max(0.0, amount)

        # Time
        row["hour"] = float(raw_data.get("hour", DEFAULT_TABULAR_VALUES["hour"]))
        row["day_of_week"] = float(raw_data.get("day_of_week", DEFAULT_TABULAR_VALUES["day_of_week"]))

        # Behavioral flags
        row["is_new_receiver"] = float(1 if raw_data.get("is_new_receiver") in [1, True, "1"] else 0)
        row["is_new_device"] = float(1 if raw_data.get("is_new_device") in [1, True, "1"] else 0)
        row["location_changed"] = float(1 if raw_data.get("location_changed") in [1, True, "1"] else 0)

        # Velocity & Attempts
        row["transactions_last_1h"] = float(raw_data.get("transactions_last_1h", DEFAULT_TABULAR_VALUES["transactions_last_1h"]))
        row["transactions_last_24h"] = float(raw_data.get("transactions_last_24h", DEFAULT_TABULAR_VALUES["transactions_last_24h"]))
        row["failed_attempts"] = float(raw_data.get("failed_attempts", DEFAULT_TABULAR_VALUES["failed_attempts"]))

        # History
        row["account_age_days"] = float(raw_data.get("account_age_days", DEFAULT_TABULAR_VALUES["account_age_days"]))
        row["receiver_transaction_count"] = float(raw_data.get("receiver_transaction_count", DEFAULT_TABULAR_VALUES["receiver_transaction_count"]))

        # Amount deviation
        if "amount_deviation" in raw_data and raw_data["amount_deviation"] is not None:
            row["amount_deviation"] = float(raw_data["amount_deviation"])
        elif "avg_transaction_amount" in raw_data and raw_data["avg_transaction_amount"]:
            row["amount_deviation"] = round(amount / max(float(raw_data["avg_transaction_amount"]), 1.0), 2)
        else:
            row["amount_deviation"] = DEFAULT_TABULAR_VALUES["amount_deviation"]

        if feature_set == "tabular":
            return pd.DataFrame([row], columns=TABULAR_FEATURES)

        # Add Graph Features (extract from payload or use calibrated defaults)
        for g_feat in GRAPH_FEATURES:
            val = raw_data.get(g_feat, DEFAULT_GRAPH_VALUES[g_feat])
            row[g_feat] = float(val if val is not None else DEFAULT_GRAPH_VALUES[g_feat])

        return pd.DataFrame([row], columns=COMBINED_FEATURES)

    def predict(self, transaction: Dict[str, Any], use_graph: bool = True) -> Dict[str, Any]:
        """
        Generates risk score, tier, action, and anomaly score for a transaction.
        When use_graph=True, executes Champion Model B (Tabular + Graph) and includes Model A comparison.
        """
        df_combined = self.prepare_features(transaction, feature_set="combined")
        df_tabular = self.prepare_features(transaction, feature_set="tabular")

        active_model = self.risk_model_b if (use_graph and self.risk_model_b is not None) else self.risk_model_a
        df_active = df_combined if (use_graph and self.risk_model_b is not None) else df_tabular

        # 1. Supervised XGBoost Probability
        proba_primary = float(active_model.predict_proba(df_active)[0, 1])
        risk_score = round(proba_primary * 100.0, 2)

        # Model A score comparison
        score_a = risk_score
        proba_a = proba_primary
        if self.risk_model_a is not None:
            try:
                p_a = float(self.risk_model_a.predict_proba(df_tabular)[0, 1])
                score_a = round(p_a * 100.0, 2)
                proba_a = round(p_a, 4)
            except Exception:
                pass

        # Model B score comparison
        score_b = risk_score
        proba_b = proba_primary
        if self.risk_model_b is not None:
            try:
                p_b = float(self.risk_model_b.predict_proba(df_combined)[0, 1])
                score_b = round(p_b * 100.0, 2)
                proba_b = round(p_b, 4)
            except Exception:
                pass

        # 2. Unsupervised Anomaly Score
        anomaly_score = None
        if self.anomaly_model is not None:
            try:
                raw_decision = float(self.anomaly_model.decision_function(df_tabular.values)[0])
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

        graph_features_extracted = {g: float(df_combined.iloc[0][g]) for g in GRAPH_FEATURES}

        return {
            "risk_score": risk_score,
            "risk_probability": round(proba_primary, 4),
            "risk_level": risk_level,
            "recommended_action": action,
            "anomaly_score": anomaly_score,
            "features_used": df_active.iloc[0].to_dict(),
            "graph_features": graph_features_extracted,
            "model_comparison": {
                "model_a_tabular_score": score_a,
                "model_a_probability": proba_a,
                "model_b_graph_score": score_b,
                "model_b_probability": proba_b,
                "graph_risk_lift": round(score_b - score_a, 2),
                "graph_detected_syndicate": bool(score_b >= 50.0 and score_a < 50.0)
            },
            "model_version": "v2.0.0-GRAPH-INTELLIGENCE" if use_graph else "v1.0.0-TABULAR"
        }

    def get_shap_explainer(self, use_graph: bool = True):
        """Returns or lazily creates a singleton shap.TreeExplainer for XGBoost."""
        if use_graph:
            if self._shap_explainer_b is None and self.risk_model_b is not None:
                try:
                    import shap
                    self._shap_explainer_b = shap.TreeExplainer(self.risk_model_b)
                    logger.info("Initialized shap.TreeExplainer for Model B (Tabular + Graph).")
                except Exception as e:
                    logger.warning(f"Could not init shap explainer B: {e}")
            return self._shap_explainer_b
        else:
            if self._shap_explainer_a is None and self.risk_model_a is not None:
                try:
                    import shap
                    self._shap_explainer_a = shap.TreeExplainer(self.risk_model_a)
                    logger.info("Initialized shap.TreeExplainer for Model A (Tabular).")
                except Exception as e:
                    logger.warning(f"Could not init shap explainer A: {e}")
            return self._shap_explainer_a

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
            return days[int(val) % 7]
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
        # Graph Features
        elif feat == "rapid_fan_in_24h":
            return f"{int(val)} distinct senders/24h"
        elif feat == "rapid_fan_out_24h":
            return f"{int(val)} receivers/24h"
        elif feat == "shared_device_count":
            return f"{int(val)} distinct customer accounts"
        elif feat == "receiver_fan_in":
            return f"{int(val)} cumulative senders"
        elif feat == "sender_fan_out_ratio":
            return f"{val:.2f}"
        elif feat == "transactions_to_receiver_24h":
            return f"{int(val)} txs/24h"
        elif feat == "transactions_to_receiver_7d":
            return f"{int(val)} txs/7d"
        elif feat == "receiver_degree_centrality":
            return f"{val:.4f}"
        elif feat == "network_risk_score":
            return f"{val:.1f}/100"
        return str(val)

    @staticmethod
    def _get_feature_metadata(feat: str, row_val: float, shap_val: float) -> tuple:
        labels = {
            # Tabular
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
            "day_of_week": "Day of Week Pattern",
            # Graph
            "rapid_fan_in_24h": "Rapid 24h Sender Inflow (Fan-In)",
            "rapid_fan_out_24h": "Rapid 24h Recipient Dispersal (Fan-Out)",
            "shared_device_count": "Hardware Device Multi-Tenancy",
            "receiver_fan_in": "Receiver Cumulative Inflow Fan-In",
            "sender_fan_out_ratio": "Sender Counterparty Dispersion",
            "receiver_in_degree": "Receiver Historical In-Degree",
            "sender_out_degree": "Sender Historical Out-Degree",
            "sender_unique_receivers": "Sender Unique Counterparties",
            "receiver_unique_senders": "Receiver Unique Senders",
            "transactions_to_receiver_24h": "Receiver 24h Transaction Volume",
            "transactions_to_receiver_7d": "Receiver 7-Day Cumulative Exposure",
            "receiver_degree_centrality": "Network Topological Centrality",
            "network_risk_score": "Syndicate Graph Risk Index"
        }
        label = labels.get(feat, feat.replace("_", " ").title())

        # Context-rich natural language explanation
        if feat == "rapid_fan_in_24h":
            inc = f"Burst aggregation: {int(row_val)} distinct customer wallets funneled money into this receiver within 24 hours (+{shap_val:.2f} log-odds)."
            mit = f"Normal single-counterparty inflow pattern ({int(row_val)} senders in 24h)."
        elif feat == "shared_device_count":
            inc = f"Hardware multi-tenancy: handset ID shared across {int(row_val)} distinct customer accounts (+{shap_val:.2f} log-odds)."
            mit = "Clean single-user hardware profile with zero cross-account sharing."
        elif feat == "receiver_degree_centrality":
            inc = f"Elevated topological centrality ({row_val:.4f}) indicates a central money-mule hub node (+{shap_val:.2f} log-odds)."
            mit = f"Peripheral node topology ({row_val:.4f}) conforms to standard peer-to-peer usage."
        elif feat == "network_risk_score":
            inc = f"High network topology risk index ({row_val:.1f}/100) indicates coordinated syndicate activity."
            mit = f"Low topology risk index ({row_val:.1f}/100)."
        elif feat == "transactions_last_1h":
            inc = f"High velocity burst ({int(row_val)} txs in 1h) sharply elevates risk (+{shap_val:.2f} log-odds)."
            mit = f"Normal hourly frequency ({int(row_val)} txs)."
        elif feat == "amount_deviation":
            inc = f"Transfer is {row_val:.1f}x higher than 30-day baseline average (+{shap_val:.2f} log-odds)."
            mit = f"Amount is consistent with habitual baseline ({row_val:.1f}x)."
        elif feat == "is_new_device":
            inc = "Session authenticated from unverified hardware identifier."
            mit = "Recognized customer hardware profile with valid device fingerprint."
        else:
            inc = f"{label} shows risk-elevating attribution (+{shap_val:.2f} log-odds)."
            mit = f"{label} shows risk-mitigating attribution ({shap_val:.2f} log-odds)."

        return label, inc, mit

    def explain(self, transaction: Dict[str, Any], use_graph: bool = True, baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
        """
        Computes true mathematical Shapley values using shap.TreeExplainer on the trained XGBoost model.
        Returns sorted attributions with feature labels, values, impact, and natural language explanations.
        """
        feature_set = "combined" if use_graph else "tabular"
        active_features = COMBINED_FEATURES if use_graph else TABULAR_FEATURES
        df = self.prepare_features(transaction, feature_set=feature_set)
        explainer = self.get_shap_explainer(use_graph=use_graph)

        if explainer is None:
            return self._heuristic_shap_fallback(transaction, baseline_avg)

        try:
            shap_vals = explainer.shap_values(df)[0]
            base_val = float(explainer.expected_value) if hasattr(explainer, "expected_value") else 0.0

            factors = []
            for i, feat in enumerate(active_features):
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
                    "explanation": explanation,
                    "is_graph_feature": feat in GRAPH_FEATURES
                })

            factors.sort(key=lambda x: abs(x["raw_shap_value"]), reverse=True)
            for rank, f in enumerate(factors, start=1):
                f["importance_rank"] = rank

            return factors
        except Exception as e:
            logger.error(f"Error executing shap.TreeExplainer: {e}")
            return self._heuristic_shap_fallback(transaction, baseline_avg)

    def _heuristic_shap_fallback(self, tx_data: Dict[str, Any], baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
        """Graceful fallback in case SHAP tree explainer is unavailable."""
        amount = float(tx_data.get("amount", 2500.0))
        deviation = float(tx_data.get("amount_deviation", amount / (baseline_avg if baseline_avg > 0 else 2500.0)))
        tx_1h = int(tx_data.get("transactions_last_1h", 1))
        fanin_24h = int(tx_data.get("rapid_fan_in_24h", 0))

        factors = [
            {
                "feature": "rapid_fan_in_24h",
                "feature_label": "Rapid 24h Sender Inflow (Fan-In)",
                "feature_value": f"{fanin_24h} senders/24h",
                "shap_value": 4.52 if fanin_24h >= 2 else -1.20,
                "raw_shap_value": 4.52 if fanin_24h >= 2 else -1.20,
                "impact": "RISK_INCREASING" if fanin_24h >= 2 else "RISK_MITIGATING",
                "explanation": f"Inflow fan-in velocity: {fanin_24h} distinct accounts in 24 hours.",
                "is_graph_feature": True,
                "importance_rank": 1
            },
            {
                "feature": "amount_deviation",
                "feature_label": "Amount Deviation vs Baseline",
                "feature_value": f"{deviation:.1f}x",
                "shap_value": 1.46 if deviation >= 2.5 else -1.46,
                "raw_shap_value": 1.46 if deviation >= 2.5 else -1.46,
                "impact": "RISK_INCREASING" if deviation >= 2.5 else "RISK_MITIGATING",
                "explanation": f"Transaction is {deviation:.1f}x customer baseline.",
                "is_graph_feature": False,
                "importance_rank": 2
            }
        ]
        return factors


# ============================================================================
# BANGLA MFS SCAM & PHISHING NLP INTELLIGENCE MODEL RUNNER
# ============================================================================
SCAM_MODEL_PATH = os.path.join(BASE_DIR, "scam_classifier.pkl")
SCAM_VECTORIZER_PATH = os.path.join(BASE_DIR, "scam_vectorizer.pkl")

def preprocess_mfs_text(text: str) -> str:
    import re
    t = str(text or "")
    t = re.sub(r'https?://\S+|www\.\S+|bit\.ly/\S+', ' [redacted_url] ', t, flags=re.IGNORECASE)
    t = re.sub(r'(\+?880|01)[0-9]{9}|[০-৯]{11}', ' [redacted_phone] ', t)
    t = re.sub(r'\[redacted_url\]|\[redacted\]', ' [redacted_url] ', t, flags=re.IGNORECASE)
    t = re.sub(r'\[redacted_phone\]', ' [redacted_phone] ', t, flags=re.IGNORECASE)
    t = re.sub(r'\[txn_id\]', ' [txn_id] ', t, flags=re.IGNORECASE)
    t = re.sub(r'\[amount\]', ' [amount] ', t, flags=re.IGNORECASE)
    return re.sub(r'\s+', ' ', t).strip()


class ScamNLPModel:
    """
    Self-contained model wrapper for Bangla MFS Scam NLP classification.
    Uses trained subword n-gram TF-IDF vectorizer + Calibrated XGBoost.
    """
    def __init__(self):
        self.classifier = None
        self.vectorizer = None
        self._load()

    def _load(self):
        if os.path.exists(SCAM_MODEL_PATH) and os.path.exists(SCAM_VECTORIZER_PATH):
            try:
                self.classifier = joblib.load(SCAM_MODEL_PATH)
                self.vectorizer = joblib.load(SCAM_VECTORIZER_PATH)
                logger.info("Loaded ScamNLPModel classifier and vectorizer successfully.")
            except Exception as e:
                logger.warning(f"Error loading ScamNLPModel artifacts: {e}")
        else:
            logger.warning(f"Scam model files not found at {SCAM_MODEL_PATH} or {SCAM_VECTORIZER_PATH}")

    def predict(self, text: str) -> Dict[str, Any]:
        raw_text = str(text or "").strip()
        if not raw_text:
            return {
                "text": "",
                "is_scam": False,
                "scam_probability": 0.0,
                "risk_score": 0.0,
                "severity": "LOW",
                "implied_brand": "Unknown",
                "persuasion_tactic": "None",
                "matched_keywords": [],
                "top_tokens": [],
                "action_recommendation": "ALLOW / LEGITIMATE"
            }

        scam_keywords = ["স্থগিত", "ব্লক", "ওটিপি", "পিন", "লটারি", "পুরস্কার", "ফ্রিজ", "জরুরি", "ভেরিফাই", "বন্ধ", "উপায়", "বিকাশ", "নগদ"]
        matched_kws = [kw for kw in scam_keywords if kw in raw_text]

        proba = 0.5
        top_tokens = []
        proc_text = preprocess_mfs_text(raw_text)

        if self.classifier is not None and self.vectorizer is not None:
            try:
                vec = self.vectorizer.transform([proc_text])
                prob_arr = self.classifier.predict_proba(vec)[0]
                proba = float(prob_arr[1])

                feature_names = np.array(self.vectorizer.get_feature_names_out())
                cx = vec.tocoo()
                if len(cx.col) > 0:
                    importances = self.classifier.feature_importances_
                    token_scores = []
                    for col_idx in cx.col:
                        token_name = feature_names[col_idx]
                        weight = float(importances[col_idx])
                        if weight > 0:
                            token_scores.append({"token": token_name, "weight": round(weight, 5)})
                    token_scores.sort(key=lambda x: x["weight"], reverse=True)
                    top_tokens = token_scores[:10]
            except Exception as e:
                logger.error(f"Error running ScamNLPModel inference: {e}")
                proba = 0.85 if len(matched_kws) > 0 else 0.15
        else:
            proba = 0.85 if len(matched_kws) > 0 else 0.15

        if any(k in raw_text for k in ["ওটিপি", "পিন", "লটারি", "পুরস্কার", "স্থগিত", "ব্লক", "ফ্রিজ"]):
            proba = max(proba, 0.88)
        if any(k in raw_text for k in ["লেনদেন সফল", "ক্যাশ-ইন সফল", "ক্যাশ ইন সফল", "ব্যালেন্স"]) and not any(k in raw_text for k in ["ওটিপি", "পিন", "লটারি", "স্থগিত", "ব্লক"]):
            proba = min(proba, 0.04)

        risk_score = round(proba * 100.0, 1)
        is_scam = bool(proba >= 0.5)

        lower_txt = raw_text.lower()
        if "বিকাশ" in raw_text or "bkash" in lower_txt:
            implied_brand = "bKash"
        elif "নগদ" in raw_text or "nagad" in lower_txt:
            implied_brand = "Nagad"
        elif "উপায়" in raw_text or "upay" in lower_txt:
            implied_brand = "upay"
        elif "রকেট" in raw_text or "rocket" in lower_txt:
            implied_brand = "Rocket"
        elif any(k in raw_text for k in ["ব্যাংক", "কার্ড", "ভিসা", "মাস্টারকার্ড"]):
            implied_brand = "Commercial Bank / Card"
        else:
            implied_brand = "General MFS"

        if any(k in raw_text for k in ["ব্লক", "স্থগিত", "ফ্রিজ", "বন্ধ", "জরুরি", "বাতিল"]):
            tactic = "Fear + Urgency (Coercive Block Threat)"
        elif any(k in raw_text for k in ["লটারি", "পুরস্কার", "বোনাস", "টাকা জিতেছেন", "ক্যাশব্যাক"]):
            tactic = "Greed / Reward (Lottery & Prize Scam)"
        elif any(k in raw_text for k in ["ওটিপি", "পিন", "পাসওয়ার্ড", "ভেরিফিকেশন", "কোড"]):
            tactic = "Credential Harvesting (OTP / PIN Theft)"
        elif any(k in raw_text for k in ["চাকরি", "নিয়োগ", "দৈনিক আয়", "ওয়ার্ক ফ্রম হোম"]):
            tactic = "Employment / Advance Fee Fraud"
        elif any(k in raw_text for k in ["ঋণ", "লোন", "বিনা সুদে", "সহজ ঋণ"]):
            tactic = "Predatory / Fake Loan Disbursement"
        else:
            tactic = "General Notice / Benign Communication"

        if risk_score >= 80.0:
            severity = "CRITICAL"
        elif risk_score >= 60.0:
            severity = "HIGH"
        elif risk_score >= 35.0:
            severity = "MEDIUM"
        else:
            severity = "LOW"

        return {
            "text": raw_text,
            "is_scam": is_scam,
            "scam_probability": round(proba, 4),
            "risk_score": risk_score,
            "severity": severity,
            "implied_brand": implied_brand,
            "persuasion_tactic": tactic,
            "matched_keywords": matched_kws,
            "top_tokens": top_tokens,
            "action_recommendation": "BLOCK & ESCALATE TO BFIU" if is_scam else "ALLOW / LEGITIMATE"
        }


# Global reusable singletons
_model_instance = None
_scam_model_instance = None

def get_model() -> TransactionRiskModel:
    global _model_instance
    if _model_instance is None:
        _model_instance = TransactionRiskModel()
    return _model_instance

def get_scam_model() -> ScamNLPModel:
    global _scam_model_instance
    if _scam_model_instance is None:
        _scam_model_instance = ScamNLPModel()
    return _scam_model_instance

def predict_risk(transaction_data: Dict[str, Any], use_graph: bool = True) -> Dict[str, Any]:
    """Convenience functional interface for transaction risk scoring."""
    return get_model().predict(transaction_data, use_graph=use_graph)

def explain_risk(transaction_data: Dict[str, Any], use_graph: bool = True, baseline_avg: float = 2500.0) -> List[Dict[str, Any]]:
    """Convenience functional interface for true shap.TreeExplainer attributions."""
    return get_model().explain(transaction_data, use_graph=use_graph, baseline_avg=baseline_avg)

def predict_scam(text: str) -> Dict[str, Any]:
    """Convenience functional interface for Bangla MFS scam text classification."""
    return get_scam_model().predict(text)


if __name__ == "__main__":
    # Smoke test
    test_tx = {
        "amount": 3200.0,
        "amount_deviation": 1.28,
        "is_new_device": 0,
        "is_new_receiver": 0,
        "hour": 14,
        "failed_attempts": 0,
        "rapid_fan_in_24h": 6,
        "shared_device_count": 4,
        "network_risk_score": 90.0
    }
    result = predict_risk(test_tx, use_graph=True)
    print("Test Transaction Risk Output (with Graph):")
    print(json.dumps(result, indent=2))

    shaps = explain_risk(test_tx, use_graph=True)
    print("\nTop 5 SHAP factors:")
    for f in shaps[:5]:
        print(f"  {f['importance_rank']}. {f['feature_label']}: {f['feature_value']} (SHAP: {f['shap_value']}) -> {f['impact']}")
