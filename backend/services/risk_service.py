import os
import time
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
from backend.engine import run_full_risk_assessment
from backend.models.transaction import Transaction, Customer


class RiskService:
    @staticmethod
    def assess_transaction_data(db: Session, tx_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Runs full risk assessment pipeline:
        1. Look up customer profile baseline from database
        2. Execute ML XGBoost / Random Forest + rule engine + typologies
        3. Compute SHAP waterfall contributions
        4. Return comprehensive prediction result
        """
        cust_id = tx_data.get("customer_id")
        cust_profile = None
        if cust_id:
            cust = db.query(Customer).filter(Customer.customer_id == cust_id).first()
            if cust:
                cust_profile = {
                    "customer_id": cust.customer_id,
                    "account_age_days": cust.account_age_days,
                    "normal_avg_amount": cust.normal_avg_amount,
                    "normal_transaction_count": cust.normal_transaction_count,
                    "primary_location": cust.primary_location,
                    "registered_device_count": cust.registered_device_count,
                    "account_created_date": cust.account_created_date
                }

        result = run_full_risk_assessment(tx_data, cust_profile)
        return result
