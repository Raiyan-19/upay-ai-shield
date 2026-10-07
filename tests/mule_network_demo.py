"""
Reproducible Mule Network Demonstration Script (AI Dev Fest Track 01)
Demonstrates the concrete value of Graph Intelligence:
Shows how individual smurfing transactions appear benign to a tabular model (Model A),
but are caught by the network graph model (Model B) due to rapid fan-in and hardware clustering.
"""

import os
import sys
import json
import joblib
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUTS_DIR = os.path.join(BASE_DIR, "outputs")
os.makedirs(OUTPUTS_DIR, exist_ok=True)
sys.path.insert(0, os.path.join(BASE_DIR, "model and chatboat"))

from models.graph_engine import TemporalTransactionGraph, GRAPH_FEATURE_NAMES

TABULAR_FEATURES = [
    "amount", "hour", "day_of_week", "is_new_receiver", "is_new_device",
    "location_changed", "transactions_last_1h", "transactions_last_24h",
    "failed_attempts", "account_age_days", "receiver_transaction_count",
    "amount_deviation"
]
COMBINED_FEATURES = TABULAR_FEATURES + GRAPH_FEATURE_NAMES

xgb_a = joblib.load(os.path.join(BASE_DIR, "model and chatboat", "models", "risk_model_a.pkl"))
xgb_b = joblib.load(os.path.join(BASE_DIR, "model and chatboat", "models", "risk_model_b.pkl"))

def run_mule_demonstration():
    print("=" * 80)
    print("  MULE NETWORK DEMONSTRATION: TABULAR (MODEL A) VS GRAPH (MODEL B)")
    print("=" * 80)

    # Setup simulated temporal graph with a fan-in mule ring
    graph = TemporalTransactionGraph()
    base_time = pd.to_datetime("2026-05-10 09:00:00")
    mule_id = "MULE-DHAKA-HUB-01"
    shared_device = "DEV-ROGUE-EMULATOR"

    # 6 feeder accounts send smurfed amounts (৳2,000 - ৳4,500) over 4 hours
    feeders = ["CUST0101", "CUST0102", "CUST0103", "CUST0104", "CUST0105", "CUST0106"]
    
    print("\nPhase 1: Pre-populating 5 feeder transfers into Mule Hub within 3 hours...")
    for i, f_id in enumerate(feeders[:-1]):
        t = base_time + timedelta(minutes=30 * i)
        amt = 2500.0 + (i * 300)
        graph.record_transaction(
            customer_id=f_id,
            receiver_id=mule_id,
            device_id=shared_device,
            amount=amt,
            timestamp=t,
            transaction_id=f"TX_FEEDER_{i+1}"
        )
        print(f"  Recorded Tx {i+1}: {f_id} -> {mule_id} | ৳{amt:,.2f} at {t.strftime('%H:%M')}")

    # Now, evaluate Transaction 6 from feeder CUST0106 to the same mule
    eval_time = base_time + timedelta(hours=3, minutes=15)
    target_tx = {
        "transaction_id": "TX_TARGET_SMURF_06",
        "customer_id": "CUST0106",
        "receiver_id": mule_id,
        "device_id": shared_device,
        "amount": 3200.0,
        "timestamp": eval_time,
        "hour": eval_time.hour,
        "day_of_week": eval_time.weekday(),
        "is_new_receiver": 0,       # Appears familiar
        "is_new_device": 0,         # Handset ID matches prior session
        "location_changed": 0,      # Same division (Dhaka)
        "transactions_last_1h": 1,  # Normal velocity for individual customer
        "transactions_last_24h": 3,
        "failed_attempts": 0,       # Zero auth failures
        "account_age_days": 650,    # Mature account
        "receiver_transaction_count": 45,
        "amount_deviation": 1.28    # Modest 1.28x baseline average
    }

    # Extract temporal graph features prior to eval_time
    g_features = graph.compute_features_for_transaction(
        customer_id=target_tx["customer_id"],
        receiver_id=target_tx["receiver_id"],
        device_id=target_tx["device_id"],
        amount=target_tx["amount"],
        timestamp=eval_time
    )

    # 1. Evaluate with Model A (Tabular Only)
    df_tab = pd.DataFrame([[target_tx[c] for c in TABULAR_FEATURES]], columns=TABULAR_FEATURES)
    prob_a = float(xgb_a.predict_proba(df_tab)[0, 1])
    score_a = round(prob_a * 100.0, 2)

    # 2. Evaluate with Model B (Tabular + Graph)
    combined_row = {**{c: target_tx[c] for c in TABULAR_FEATURES}, **g_features}
    df_all = pd.DataFrame([[combined_row[c] for c in COMBINED_FEATURES]], columns=COMBINED_FEATURES)
    prob_b = float(xgb_b.predict_proba(df_all)[0, 1])
    score_b = round(prob_b * 100.0, 2)

    print("\n" + "-" * 80)
    print("EVALUATING INCOMING ৳3,200 TRANSACTION (TX_TARGET_SMURF_06):")
    print(f"  Customer: {target_tx['customer_id']} | Receiver: {target_tx['receiver_id']}")
    print(f"  Amount: ৳{target_tx['amount']:,.2f} | Amount Deviation: {target_tx['amount_deviation']}x")
    print(f"  Failed Attempts: 0 | New Device: 0 | New Receiver: 0 | Location Changed: 0")
    print("-" * 80)

    print("\n[TEMPORAL GRAPH SIGNALS EXTRACTED BEFORE T]:")
    print(f"  rapid_fan_in_24h:            {g_features['rapid_fan_in_24h']} distinct customer senders in 24h")
    print(f"  receiver_fan_in:             {g_features['receiver_fan_in']} cumulative senders")
    print(f"  shared_device_count:         {g_features['shared_device_count']} distinct customer accounts on device")
    print(f"  receiver_degree_centrality:  {g_features['receiver_degree_centrality']:.4f}")
    print(f"  network_risk_score:          {g_features['network_risk_score']}/100")

    print("\n" + "=" * 80)
    print(f"MODEL A (TABULAR ONLY):")
    print(f"  Risk Probability: {prob_a:.4f} | Risk Score: {score_a}/100")
    print(f"  Decision:         {'CONTINUE (MISSED FRAUD)' if score_a < 50 else 'FLAGGED'}")
    print(f"  Explanation:      Tabular engine sees benign ৳3,200 transfer during daytime with 0 failed auth.")

    print(f"\nMODEL B (TABULAR + GRAPH INTELLIGENCE):")
    print(f"  Risk Probability: {prob_b:.4f} | Risk Score: {score_b}/100")
    print(f"  Decision:         {'HUMAN_REVIEW / 2FA (CAUGHT BY GRAPH)' if score_b >= 50 else 'CONTINUE'}")
    print(f"  Explanation:      Graph engine identifies rapid 5-sender fan-in aggregation and shared hardware.")
    print("=" * 80)

    demo_result = {
        "target_transaction": target_tx["transaction_id"],
        "amount": target_tx["amount"],
        "model_a_tabular": {
            "risk_score": score_a,
            "probability": prob_a,
            "status": "FALSE_NEGATIVE_UNDER_THRESHOLD" if score_a < 50 else "DETECTED"
        },
        "model_b_graph": {
            "risk_score": score_b,
            "probability": prob_b,
            "status": "TRUE_POSITIVE_DETECTED" if score_b >= 50 else "UNDER_THRESHOLD"
        },
        "graph_evidence": g_features
    }

    with open(os.path.join(OUTPUTS_DIR, "mule_demonstration_results.json"), "w", encoding="utf-8") as f:
        json.dump(demo_result, f, indent=2)

    return demo_result

if __name__ == "__main__":
    run_mule_demonstration()
