"""
Model A vs Model B Temporal Ablation & Evaluation Pipeline
Evaluates:
- Baseline 1: Logistic Regression (Tabular)
- Baseline 2: Random Forest (Tabular)
- Model A: XGBoost (Tabular Only - 12 Canonical Features)
- Model B: XGBoost (Tabular + 15 Temporal Graph Features)

Strict Evaluation Protocol:
- Chronological temporal train/val/test split (70% Train, 15% Val, 15% Test).
- Untouched holdout test set (3,000 chronological transactions).
- Zero data leakage: graph features computed prior to event timestamps.
- Realistic low-prevalence evaluation metrics (Precision, Recall, F1, PR-AUC, ROC-AUC, FPR, Alert Volume).
"""

import os
import sys
import json
import logging
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timezone
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestClassifier
from xgboost import XGBClassifier
from sklearn.metrics import (
    precision_score, recall_score, f1_score, roc_auc_score,
    average_precision_score, confusion_matrix
)

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(BASE_DIR, "model and chatboat"))

from models.graph_engine import TemporalTransactionGraph, GRAPH_FEATURE_NAMES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("graph_ablation")

CSV_PATH = os.path.join(BASE_DIR, "data", "upay_ai_shield_20000_transactions.csv")
MODELS_DIR = os.path.join(BASE_DIR, "model and chatboat", "models")
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(MODELS_DIR, exist_ok=True)
os.makedirs(OUTPUTS_DIR, exist_ok=True)

TABULAR_FEATURES = [
    "amount", "hour", "day_of_week", "is_new_receiver", "is_new_device",
    "location_changed", "transactions_last_1h", "transactions_last_24h",
    "failed_attempts", "account_age_days", "receiver_transaction_count",
    "amount_deviation"
]


def run_pipeline():
    logger.info("Loading transaction dataset...")
    df = pd.read_csv(CSV_PATH)
    df['timestamp'] = pd.to_datetime(df['timestamp'])
    # Strict chronological ordering
    df = df.sort_values('timestamp').reset_index(drop=True)
    n_total = len(df)
    logger.info(f"Loaded {n_total} transactions chronologically ({df['timestamp'].min()} to {df['timestamp'].max()}).")

    # Step 1: Extract Temporal Graph Features sequentially with zero future leakage
    logger.info("Generating temporal graph features...")
    graph = TemporalTransactionGraph()
    graph_records = []

    for _, row in df.iterrows():
        g_feat = graph.compute_features_for_transaction(
            customer_id=row['customer_id'],
            receiver_id=row['receiver_id'],
            device_id=row['device_id'],
            amount=float(row['amount']),
            timestamp=row['timestamp']
        )
        graph_records.append(g_feat)

        graph.record_transaction(
            customer_id=row['customer_id'],
            receiver_id=row['receiver_id'],
            device_id=row['device_id'],
            amount=float(row['amount']),
            timestamp=row['timestamp'],
            channel=row.get('channel', 'APP'),
            transaction_type=row.get('transaction_type', 'SEND_MONEY'),
            transaction_id=row.get('transaction_id', '')
        )

    graph_df = pd.DataFrame(graph_records)
    full_df = pd.concat([df, graph_df], axis=1)

    # Step 2: Chronological Train / Val / Test Split
    # Oldest 70% -> Train (14,000)
    # Middle 15% -> Val (3,000)
    # Latest 15% -> Test (3,000)
    n_train = int(n_total * 0.70)
    n_val = int(n_total * 0.15)
    
    train_df = full_df.iloc[:n_train].copy()
    val_df = full_df.iloc[n_train:n_train+n_val].copy()
    test_df = full_df.iloc[n_train+n_val:].copy()

    logger.info(f"Train split: {len(train_df)} rows ({train_df['is_fraud'].sum()} fraud, {train_df['is_fraud'].mean()*100:.2f}%)")
    logger.info(f"Val split:   {len(val_df)} rows ({val_df['is_fraud'].sum()} fraud, {val_df['is_fraud'].mean()*100:.2f}%)")
    logger.info(f"Test split:  {len(test_df)} rows ({test_df['is_fraud'].sum()} fraud, {test_df['is_fraud'].mean()*100:.2f}%)")

    # Prepare feature sets
    X_train_tab = train_df[TABULAR_FEATURES].fillna(0).values
    X_val_tab = val_df[TABULAR_FEATURES].fillna(0).values
    X_test_tab = test_df[TABULAR_FEATURES].fillna(0).values

    COMBINED_FEATURES = TABULAR_FEATURES + GRAPH_FEATURE_NAMES
    X_train_all = train_df[COMBINED_FEATURES].fillna(0).values
    X_val_all = val_df[COMBINED_FEATURES].fillna(0).values
    X_test_all = test_df[COMBINED_FEATURES].fillna(0).values

    y_train = train_df['is_fraud'].values
    y_val = val_df['is_fraud'].values
    y_test = test_df['is_fraud'].values

    # Step 3: Train Models
    # Model 1: Logistic Regression (Tabular)
    logger.info("Training Logistic Regression (Tabular)...")
    lr = LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)
    lr.fit(X_train_tab, y_train)

    # Model 2: Random Forest (Tabular)
    logger.info("Training Random Forest (Tabular)...")
    rf = RandomForestClassifier(n_estimators=100, max_depth=8, class_weight="balanced", random_state=42, n_jobs=-1)
    rf.fit(X_train_tab, y_train)

    # Model A: XGBoost (Tabular Only)
    logger.info("Training Model A: XGBoost (Tabular Only)...")
    scale_pos = (len(y_train) - sum(y_train)) / max(sum(y_train), 1)
    xgb_a = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb_a.fit(train_df[TABULAR_FEATURES].fillna(0), y_train)

    # Model B: XGBoost (Tabular + Graph Features)
    logger.info("Training Model B: XGBoost (Tabular + Graph)...")
    xgb_b = XGBClassifier(
        n_estimators=120,
        max_depth=5,
        learning_rate=0.08,
        scale_pos_weight=scale_pos,
        eval_metric="logloss",
        random_state=42,
        n_jobs=-1
    )
    xgb_b.fit(train_df[COMBINED_FEATURES].fillna(0), y_train)

    # Step 4: Strict Chronological Holdout Evaluation
    models = {
        "Logistic Regression (Tabular)": (lr, X_test_tab),
        "Random Forest (Tabular)": (rf, X_test_tab),
        "Model A: XGBoost (Tabular Only)": (xgb_a, test_df[TABULAR_FEATURES].fillna(0)),
        "Model B: XGBoost (Tabular + Graph)": (xgb_b, test_df[COMBINED_FEATURES].fillna(0))
    }

    results = {}
    cutoff_threshold = 0.50

    for m_name, (m_obj, X_eval) in models.items():
        proba = m_obj.predict_proba(X_eval)[:, 1]
        preds = (proba >= cutoff_threshold).astype(int)

        tn, fp, fn, tp = confusion_matrix(y_test, preds).ravel()
        prec = float(precision_score(y_test, preds, zero_division=0))
        rec = float(recall_score(y_test, preds, zero_division=0))
        f1 = float(f1_score(y_test, preds, zero_division=0))
        pr_auc = float(average_precision_score(y_test, proba))
        roc_auc = float(roc_auc_score(y_test, proba))
        fpr = float(fp / (fp + tn)) if (fp + tn) > 0 else 0.0
        alerts_per_100k = int((preds.sum() / len(preds)) * 100000)

        results[m_name] = {
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "pr_auc": round(pr_auc, 4),
            "roc_auc": round(roc_auc, 4),
            "false_positive_rate": round(fpr, 4),
            "confusion_matrix": {
                "true_negatives": int(tn),
                "false_positives": int(fp),
                "false_negatives": int(fn),
                "true_positives": int(tp)
            },
            "alerts_per_100k_txs": alerts_per_100k,
            "total_test_samples": len(y_test),
            "actual_frauds_in_test": int(y_test.sum())
        }

    # Step 5: Save Model Artifacts
    joblib.dump(xgb_a, os.path.join(MODELS_DIR, "risk_model_a.pkl"))
    joblib.dump(xgb_b, os.path.join(MODELS_DIR, "risk_model_b.pkl"))
    # Champion deployment model: Point risk_model.pkl to Model B
    joblib.dump(xgb_b, os.path.join(MODELS_DIR, "risk_model.pkl"))

    # Save feature schemas
    with open(os.path.join(MODELS_DIR, "feature_schema.json"), "w", encoding="utf-8") as f:
        json.dump({
            "tabular_features": TABULAR_FEATURES,
            "graph_features": GRAPH_FEATURE_NAMES,
            "all_features": COMBINED_FEATURES
        }, f, indent=2)

    # Save benchmark metrics to outputs/graph_benchmark.json
    benchmark_payload = {
        "title": "upay AI Shield — Model A vs Model B Temporal Graph Ablation Benchmark",
        "evaluation_protocol": "Strict Chronological Holdout (Oldest 70% Train, Next 15% Val, Latest 15% Test)",
        "temporal_window_train": f"{train_df['timestamp'].min().isoformat()} to {train_df['timestamp'].max().isoformat()}",
        "temporal_window_test": f"{test_df['timestamp'].min().isoformat()} to {test_df['timestamp'].max().isoformat()}",
        "test_set_size": len(test_df),
        "test_fraud_prevalence": round(float(y_test.mean()), 4),
        "evaluated_at": datetime.now(timezone.utc).isoformat(),
        "models_benchmark": results,
        "delta_model_b_vs_model_a": {
            "pr_auc_lift": round(results["Model B: XGBoost (Tabular + Graph)"]["pr_auc"] - results["Model A: XGBoost (Tabular Only)"]["pr_auc"], 4),
            "f1_lift": round(results["Model B: XGBoost (Tabular + Graph)"]["f1_score"] - results["Model A: XGBoost (Tabular Only)"]["f1_score"], 4),
            "recall_lift": round(results["Model B: XGBoost (Tabular + Graph)"]["recall"] - results["Model A: XGBoost (Tabular Only)"]["recall"], 4),
            "fpr_reduction": round(results["Model A: XGBoost (Tabular Only)"]["false_positive_rate"] - results["Model B: XGBoost (Tabular + Graph)"]["false_positive_rate"], 4)
        }
    }

    with open(os.path.join(OUTPUTS_DIR, "graph_benchmark.json"), "w", encoding="utf-8") as f:
        json.dump(benchmark_payload, f, indent=2)

    logger.info("=== BENCHMARK COMPLETE ===")
    print("\n" + "="*80)
    print("  MODEL A vs MODEL B TEMPORAL HOLD-OUT RESULTS (ZERO DATA LEAKAGE)")
    print("="*80)
    for name, m in results.items():
        print(f"[{name}]")
        print(f"  Precision: {m['precision']*100:.2f}% | Recall: {m['recall']*100:.2f}% | F1: {m['f1_score']*100:.2f}%")
        print(f"  PR-AUC: {m['pr_auc']:.4f} | ROC-AUC: {m['roc_auc']:.4f} | FPR: {m['false_positive_rate']*100:.2f}%")
        print(f"  Confusion Matrix: TP={m['confusion_matrix']['true_positives']}, FP={m['confusion_matrix']['false_positives']}, FN={m['confusion_matrix']['false_negatives']}, TN={m['confusion_matrix']['true_negatives']}")
        print(f"  Alert Volume: {m['alerts_per_100k_txs']:,} per 100k transactions\n")

    return benchmark_payload


if __name__ == "__main__":
    run_pipeline()
