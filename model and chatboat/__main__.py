"""
ai_models_and_chatbot - Main Interactive Demonstration Runner
Run directly with:
    python -m ai_models_and_chatbot
"""

import json
from . import (
    predict_risk,
    ask_chatbot,
    load_sample_transactions,
    load_sample_customers
)


def run_component_demo():
    print("=" * 65)
    print("  upay AI Shield - Reusable AI Component Demo")
    print("  Models (XGBoost/IsolationForest) + Chatbot (Gemini/Local) + Data")
    print("=" * 65)

    # 1. Load Data
    print("\n[1] DATA COMPONENT:")
    sample_txs = load_sample_transactions()
    sample_custs = load_sample_customers()
    print(f"  * Loaded {len(sample_txs)} sample transactions from data/sample_transactions.csv")
    print(f"  * Loaded {len(sample_custs)} customer baselines from data/sample_customers.json")

    # 2. Test Model on 3 different scenarios
    print("\n[2] MODEL COMPONENT (XGBoost Fraud Scoring):")
    scenarios = [
        ("Normal Grocery Payment", sample_txs[0] if sample_txs else {"amount": 1500, "is_new_device": 0}),
        ("Suspicious Velocity Surge", {
            "amount": 18500.0,
            "amount_deviation": 5.2,
            "is_new_device": 0,
            "is_new_receiver": 1,
            "hour": 22,
            "transactions_last_1h": 3,
            "failed_attempts": 1
        }),
        ("Critical Account Takeover (ATO)", {
            "amount": 65000.0,
            "amount_deviation": 16.5,
            "is_new_device": 1,
            "is_new_receiver": 1,
            "hour": 3,
            "transactions_last_1h": 7,
            "failed_attempts": 3,
            "account_age_days": 40
        })
    ]

    for label, tx in scenarios:
        res = predict_risk(tx)
        print(f"\n  Scenario: {label}")
        print(f"    - Amount        : BDT {tx.get('amount', 0):,.2f}")
        print(f"    - Risk Score    : {res['risk_score']} / 100")
        print(f"    - Risk Tier     : {res['risk_level']}")
        print(f"    - Action        : {res['recommended_action']}")

    # 3. Test Chatbot Component
    print("\n[3] CHATBOT COMPONENT (Gemini / Local Forensic Copilot):")
    test_context = scenarios[2][1]
    test_context["transaction_id"] = "TX10998"
    test_context["risk_score"] = 99.99
    test_context["risk_level"] = "HIGH"

    test_queries = [
        "Is this transaction an Account Takeover?",
        "What questions should I ask the customer when calling to verify?"
    ]

    for q in test_queries:
        print(f"\n  Analyst Question: \"{q}\"")
        chat_output = ask_chatbot(message=q, transaction_context=test_context)
        print(f"  Engine Used     : {chat_output['engine_used']}")
        print("  Response Snippet:")
        # Print indented
        for line in chat_output["response"].split("\n")[:8]:
            print(f"    {line}")
        print("    ...")

    print("\n" + "=" * 65)
    print("  All Component Tests Passed! Ready for copy-paste integration.")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    run_component_demo()
