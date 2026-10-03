from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class TransactionCreate(BaseModel):
    transaction_id: Optional[str] = None
    customer_id: str
    amount: float = Field(..., gt=0)
    transaction_type: str
    channel: str = "App"
    device_id: Optional[str] = "DEV-9921"
    ip_address: Optional[str] = "103.114.98.12"
    location: Optional[str] = "Dhaka"
    recipient_account: Optional[str] = "01889922331"
    is_new_recipient: bool = False
    is_night_transaction: bool = False
    failed_pin_attempts_last_hour: int = 0
    device_changed_recently: bool = False
    sim_changed_recently: bool = False
    velocity_1h_count: int = 1
    velocity_24h_count: int = 1
    amount_deviation_score: float = 1.0


class TransactionResponse(BaseModel):
    transaction_id: str
    customer_id: str
    amount: float
    transaction_type: str
    channel: str
    device_id: str
    ip_address: str
    location: str
    recipient_account: Optional[str]
    is_new_recipient: bool
    is_night_transaction: bool
    failed_pin_attempts_last_hour: int
    device_changed_recently: bool
    sim_changed_recently: bool
    velocity_1h_count: int
    velocity_24h_count: int
    amount_deviation_score: float
    risk_score: float
    decision_action: str
    risk_level: str
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class RiskAssessmentResult(BaseModel):
    transaction_id: str
    risk_score: float
    probability: float
    risk_level: str
    decision_action: str
    model_version: str
    typologies_triggered: List[Dict[str, Any]]
    compound_threat: Optional[Dict[str, Any]] = None
    shap_factors: List[Dict[str, Any]]
    processing_time_ms: float


class AnalystFeedbackCreate(BaseModel):
    transaction_id: str
    decision: str = Field(..., description="SUSPICIOUS, LEGITIMATE, or NEEDS_REVIEW")
    comment: Optional[str] = ""
