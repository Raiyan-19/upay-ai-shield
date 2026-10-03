"""
ai_models_and_chatbot - Data Loader Utility
Provides easy access to sample transactions, customer baselines, and test data.
"""

import os
import json
from typing import List, Dict, Any, Optional
import pandas as pd

DATA_DIR = os.path.dirname(os.path.abspath(__file__))
TX_CSV_PATH = os.path.join(DATA_DIR, "sample_transactions.csv")
CUST_JSON_PATH = os.path.join(DATA_DIR, "sample_customers.json")


def load_sample_transactions() -> List[Dict[str, Any]]:
    """Loads sample transactions as list of dictionaries."""
    if not os.path.exists(TX_CSV_PATH):
        return []
    df = pd.read_csv(TX_CSV_PATH)
    return df.to_dict(orient="records")


def load_sample_customers() -> List[Dict[str, Any]]:
    """Loads sample customer baseline profiles."""
    if not os.path.exists(CUST_JSON_PATH):
        return []
    with open(CUST_JSON_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_transaction_by_id(tx_id: str) -> Optional[Dict[str, Any]]:
    """Fetches a specific transaction by transaction_id."""
    for tx in load_sample_transactions():
        if tx.get("transaction_id") == tx_id:
            return tx
    return None


def get_customer_by_id(cust_id: str) -> Optional[Dict[str, Any]]:
    """Fetches customer baseline by customer_id."""
    for cust in load_sample_customers():
        if cust.get("customer_id") == cust_id:
            return cust
    return None


if __name__ == "__main__":
    txs = load_sample_transactions()
    custs = load_sample_customers()
    print(f"Loaded {len(txs)} sample transactions.")
    print(f"Loaded {len(custs)} sample customers.")
    if txs:
        print("Sample TX 0 ID:", txs[0].get("transaction_id"), "Amount:", txs[0].get("amount"))
