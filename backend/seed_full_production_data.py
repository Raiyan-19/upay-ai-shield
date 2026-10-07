"""
Production Database Seeder for upay AI Shield Enterprise.
Ingests:
- 5,000 customer baseline profiles from data/upay_ai_shield_5000_customers (1).csv
- 20,000 calibrated transactions from data/upay_ai_shield_20000_transactions (1).csv
- Auto-generates statutory Case Management records & audit event logs for high/critical transactions.
"""

import os
import csv
import sys
import time
from datetime import datetime, timezone, timedelta

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from backend.models.base import engine, SessionLocal, Base
from backend.models.transaction import Customer, Transaction
from backend.models.case import Case, CaseEvent
from backend.models.audit import AnalystFeedback, AuditLog
from backend.services.auth_service import AuthService

CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "upay_ai_shield_5000_customers.csv")
if not os.path.exists(CUSTOMERS_CSV):
    CUSTOMERS_CSV = os.path.join(BASE_DIR, "data", "upay_ai_shield_5000_customers (1).csv")

TRANSACTIONS_CSV = os.path.join(BASE_DIR, "data", "upay_ai_shield_20000_transactions.csv")
if not os.path.exists(TRANSACTIONS_CSV):
    TRANSACTIONS_CSV = os.path.join(BASE_DIR, "data", "upay_ai_shield_20000_transactions (1).csv")


def seed_production_database():
    start_time = time.time()
    print("=" * 65)
    print("  upay AI Shield — Ingesting Production Datasets into SQLite")
    print("=" * 65)

    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        # 1. Ensure seed personnel accounts exist
        AuthService.seed_initial_users(db)
        print("  [1/4] Personnel accounts verified (ADMIN, SENIOR_OFFICER, ANALYST, VIEWER).")

        # 2. Ingest 5,000 Customer Baseline Profiles
        print(f"  [2/4] Reading {CUSTOMERS_CSV}...")
        existing_cust_ids = set(r[0] for r in db.query(Customer.customer_id).all())
        customer_batch = []
        now_dt = datetime.now(timezone.utc)

        with open(CUSTOMERS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["customer_id"]
                if cid not in existing_cust_ids:
                    customer_batch.append({
                        "customer_id": cid,
                        "account_age_days": int(row.get("account_age_days", 730)),
                        "normal_avg_amount": float(row.get("normal_avg_amount", 2500.0)),
                        "normal_transaction_count": int(row.get("normal_transaction_count", 10)),
                        "primary_location": row.get("primary_location", "Dhaka"),
                        "registered_device_count": int(row.get("registered_device_count", 2)),
                        "account_created_date": row.get("account_created_date", "2022-01-01"),
                        "created_at": now_dt,
                        "updated_at": now_dt
                    })
                    existing_cust_ids.add(cid)

        if customer_batch:
            db.bulk_insert_mappings(Customer, customer_batch)
            db.commit()
            print(f"        -> Ingested {len(customer_batch):,} new customer baseline profiles.")
        else:
            print(f"        -> Customer table already contains {len(existing_cust_ids):,} profiles.")

        # 3. Ingest 20,000 Transactions Ledger
        print(f"  [3/4] Reading {TRANSACTIONS_CSV}...")
        existing_tx_ids = set(r[0] for r in db.query(Transaction.transaction_id).all())
        tx_batch = []
        high_risk_txs = []

        with open(TRANSACTIONS_CSV, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                tx_id = row["transaction_id"]
                if tx_id not in existing_tx_ids:
                    score = float(row.get("demo_risk_score", 10.0))
                    risk_lvl = row.get("risk_level", "LOW").upper()
                    
                    tx_dict = {
                        "transaction_id": tx_id,
                        "customer_id": row["customer_id"],
                        "amount": float(row.get("amount", 0.0)),
                        "timestamp": row.get("timestamp", "2026-10-03 14:00:00"),
                        "hour": int(row.get("hour", 14)),
                        "day_of_week": int(row.get("day_of_week", 3)),
                        "transaction_type": row.get("transaction_type", "SEND_MONEY"),
                        "channel": row.get("channel", "APP"),
                        "receiver_id": row.get("receiver_id", "RECP-0000000000"),
                        "is_new_receiver": int(row.get("is_new_receiver", 0)),
                        "device_id": row.get("device_id", "DEV-000000"),
                        "is_new_device": int(row.get("is_new_device", 0)),
                        "location": row.get("location", "Dhaka"),
                        "location_changed": int(row.get("location_changed", 0)),
                        "transactions_last_1h": int(row.get("transactions_last_1h", 1)),
                        "transactions_last_24h": int(row.get("transactions_last_24h", 4)),
                        "failed_attempts": int(row.get("failed_attempts", 0)),
                        "account_age_days": int(row.get("account_age_days", 730)),
                        "receiver_transaction_count": int(row.get("receiver_transaction_count", 25)),
                        "avg_transaction_amount": float(row.get("avg_transaction_amount", 2500.0)),
                        "amount_deviation": float(row.get("amount_deviation", 1.0)),
                        "is_fraud": int(row.get("is_fraud", 0)),
                        "demo_risk_score": score,
                        "risk_level": risk_lvl,
                        "created_at": now_dt
                    }
                    tx_batch.append(tx_dict)
                    existing_tx_ids.add(tx_id)

                    if risk_lvl in ["HIGH", "CRITICAL"] or score >= 75.0:
                        high_risk_txs.append(tx_dict)

        if tx_batch:
            # Batch in chunks of 2,000 for SQLite performance
            chunk_size = 2000
            for i in range(0, len(tx_batch), chunk_size):
                chunk = tx_batch[i:i + chunk_size]
                db.bulk_insert_mappings(Transaction, chunk)
                db.commit()
            print(f"        -> Ingested {len(tx_batch):,} production transactions into ledger.")
        else:
            print(f"        -> Transactions table already contains {len(existing_tx_ids):,} transactions.")

        # 4. Generate Formal Case Management Records for High-Risk Transactions
        print("  [4/4] Indexing High-Risk Transactions into Case Management...")
        from backend.enrich_cases import enrich_cases_database
        enrich_cases_database()

        # Log system audit
        db.add(AuditLog(
            username="system",
            role="ADMIN",
            action="DATASET_INGESTION_COMPLETED",
            resource_type="database",
            resource_id="upay_ai_shield.db",
            details=f"Production datasets synchronized: {len(customer_batch)} customers, {len(tx_batch)} transactions, {len(new_cases)} cases."
        ))
        db.commit()

        elapsed = round(time.time() - start_time, 2)
        print("\n" + "=" * 65)
        print(f"  SUCCESS! Ingestion completed in {elapsed} seconds.")
        print(f"  Total Customers in DB:    {db.query(Customer).count():,}")
        print(f"  Total Transactions in DB: {db.query(Transaction).count():,}")
        print(f"  Total Cases in DB:        {db.query(Case).count():,}")
        print("=" * 65 + "\n")

    except Exception as e:
        db.rollback()
        print(f"  [ERROR] Ingestion failed: {e}")
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    seed_production_database()
