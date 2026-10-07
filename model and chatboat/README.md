# Reusable AI Component: ML Risk Model & Gemini Chatbot
**Portable, Zero-Dependency AI Package for Transaction Fraud Scoring & Forensic Chat Investigation**

---

## 🌟 1. Component Overview (এই ফোল্ডারটি কীসের জন্য)

This folder (`ai_models_and_chatbot`) is an isolated, reusable AI component containing **ONLY the trained models, the Gemini/local forensic chatbot, and representative sample data**. 

It is designed to be **copied and pasted directly into ANY new application** (new backend & new frontend), allowing an AI coding assistant (or human developer) to immediately wire it into your system without touching the original engine or codebase.

### What is inside this folder:
```
ai_models_and_chatbot/
├── models/                     # 1. THE MODEL PART
│   ├── risk_model.pkl          # Trained XGBoost Classifier binary
│   ├── anomaly_model.pkl       # Unsupervised Isolation Forest binary
│   ├── model_metadata.json     # Hyperparameters, evaluation metrics, thresholds
│   ├── feature_schema.json     # 12 canonical features with statistics & ranges
│   └── model_runner.py         # Reusable 1-line prediction function: predict_risk(tx)
│
├── chatbot/                    # 2. THE GEMINI CHATBOT PART
│   ├── gemini_assistant.py     # Google Gemini API connector with evidence grounding
│   ├── local_assistant.py      # Zero-overhead offline local chatbot fallback
│   └── chat_runner.py          # Unified entry-point: ask_chatbot(msg, tx_context)
│
├── data/                       # 3. THE DATA PART
│   ├── sample_transactions.csv # 55 representative transactions (Normal, Medium, Fraud)
│   ├── sample_customers.json   # 25 customer behavioral baselines
│   └── data_loader.py          # Data helpers: load_sample_transactions(), get_by_id()
│
├── README.md                   # Complete documentation (this file)
└── train_and_benchmark.py      # Dual-engine ML & NLP training & benchmark pipeline
```

---

## 🧠 2. Model Part: Detailed Specifications & Rationale

### Model Architecture:
- **Primary Algorithm:** XGBoost (`XGBClassifier`) with 250 estimators, learning rate `0.04`, max depth `5`, calibrated `scale_pos_weight = 11.7` for class imbalance.
- **Secondary Algorithm:** Unsupervised Isolation Forest for novelty/anomaly detection.
- **Trained Dataset:** 20,000 synthetic Bangladesh MFS transaction records calibrated against real-world mobile wallet typologies (ATO, social engineering scams, velocity bursts).
- **Evaluation Performance:** Stratified Test Set ROC-AUC: `1.0`, Precision: `1.0`, Recall: `1.0` (on synthetic benchmark).

### The 12 Canonical Features:
Every transaction is evaluated using these **12 features** (missing values auto-defaulted):

| Feature Key | Type | Description | Safe Default |
| :--- | :--- | :--- | :--- |
| `amount` | `float` | Nominal transaction amount in Bangladesh Taka (৳ / BDT). | `2500.0` |
| `amount_deviation` | `float` | Ratio of amount to customer's historical average (`amount / avg_amount`). | `1.0` |
| `is_new_device` | `int (0/1)` | `1` if session authenticated on an unverified device identifier. | `0` |
| `is_new_receiver` | `int (0/1)` | `1` if recipient account has never received money from this sender before. | `0` |
| `location_changed` | `int (0/1)` | `1` if transaction IP/GPS city deviates from historical user cluster. | `0` |
| `hour` | `int (0-23)`| Hour of execution (0 to 23). Off-hours (01:00 - 04:59) elevate risk. | `14` |
| `day_of_week` | `int (0-6)` | Day of week (`0` = Monday, `6` = Sunday). | `3` |
| `transactions_last_1h` | `int` | Number of transactions initiated by sender in the last 60 minutes. | `1` |
| `transactions_last_24h`| `int` | Number of transactions initiated by sender in the last 24 hours. | `4` |
| `failed_attempts` | `int` | Count of consecutive failed PIN/password attempts preceding transfer. | `0` |
| `account_age_days` | `int` | Age of customer account in days. Accounts < 60 days have higher scrutiny. | `730` |
| `receiver_transaction_count`| `int` | Total historical transfers received by beneficiary account. | `25` |

### Calibrated Risk Tiers & Governance Rules:
- **Score 0.0 to 49.99 (`LOW`)** $\rightarrow$ **Action: `CONTINUE`** (Instant execution)
- **Score 50.0 to 79.99 (`MEDIUM`)** $\rightarrow$ **Action: `ADDITIONAL_REVIEW`** (Trigger 2FA / SMS OTP challenge)
- **Score 80.0 to 100.0 (`HIGH`)** $\rightarrow$ **Action: `HUMAN_REVIEW`** (Route to compliance analyst queue)

### How to use the Model in 3 lines:
```python
from ai_models_and_chatbot import predict_risk

result = predict_risk({"amount": 45000.0, "amount_deviation": 10.5, "is_new_device": 1})
print(result["risk_score"])         # e.g. 99.99
print(result["risk_level"])         # "HIGH"
print(result["recommended_action"]) # "HUMAN_REVIEW"
```

---

## 🤖 3. Chatbot Part: Gemini & Local Forensic Assistant

The chatbot component acts as an **interactive forensic risk copilot for human analysts**.

### Dual-Engine Capability:
1. **Google Gemini Mode:** If `GEMINI_API_KEY` is provided, it connects to Google Gemini (rotates through `gemini-2.5-flash`, `gemini-flash-latest`), providing rich, contextual investigation synthesis.
2. **Local Intelligent Fallback Mode:** If no API key is provided or the device is offline, it automatically falls back to the embedded rule-and-telemetry intelligence engine. **It will never crash or return empty responses!**

### What the Chatbot Can Answer:
- *"Why was this transaction flagged as high risk?"* $\rightarrow$ Analyzes device, velocity, and amount deviation.
- *"Is this transaction an Account Takeover (ATO)?"* $\rightarrow$ Checks device ID, failed attempts, and night-time fund draining.
- *"What should I ask the customer when calling to verify?"* $\rightarrow$ Returns a 4-point verification checklist.
- *"Is this a scam or mule account?"* $\rightarrow$ Evaluates beneficiary transaction history and surge ratio.

### How to use the Chatbot in 3 lines:
```python
from ai_models_and_chatbot import ask_chatbot

context = {"transaction_id": "TX1001", "amount": 35000.0, "amount_deviation": 8.0, "is_new_device": 1}
response = ask_chatbot("Why is this transaction risky?", transaction_context=context)

print(response["response"])    # The AI forensic explanation
print(response["engine_used"]) # "gemini-api" or "local-intelligence-engine"
```

---

## 📁 4. Data Part: Sample Datasets & Loader Utility

The `data/` folder includes ready-to-test data so you can test the models and chatbot immediately:
- **`sample_transactions.csv`**: 55 complete transactions covering normal low-risk payments, medium-risk volume surges, and critical fraud cases (ATO & impersonation scams).
- **`sample_customers.json`**: 25 customer profile baselines with normal spending habits, account age, and trusted device counts.
- **`data_loader.py`**: Clean loader functions.

```python
from ai_models_and_chatbot import load_sample_transactions, load_sample_customers

transactions = load_sample_transactions() # List of 55 dicts
customers = load_sample_customers()       # List of 25 dicts

# Test the first transaction against the model:
from ai_models_and_chatbot import predict_risk
print(predict_risk(transactions[0]))
```

---

## 🚀 5. How to Integrate into a NEW Project (Backend & Frontend)

### Step 1: Copy this folder
Simply copy the entire `ai_models_and_chatbot/` folder into your new project root.

### Step 2: Install dependencies
```bash
pip install xgboost scikit-learn pandas numpy joblib
# Optional for Gemini API:
pip install google-genai
```

### Step 3: Wire into your Backend (e.g., FastAPI / Flask / Express)
Expose two simple endpoints in your new backend:

```python
from fastapi import FastAPI
from ai_models_and_chatbot import predict_risk, ask_chatbot

app = FastAPI()

@app.post("/api/risk/evaluate")
def evaluate(transaction: dict):
    return predict_risk(transaction)

@app.post("/api/chat/inquire")
def chat(payload: dict):
    return ask_chatbot(
        message=payload.get("message"),
        transaction_context=payload.get("transaction")
    )
```

### Step 4: Wire into your Frontend (React / Vue / HTML)
- When a user submits or views a transaction, `POST` to `/api/risk/evaluate` to render the **Risk Score Badge (0-100)** and **Action (CONTINUE / 2FA / REVIEW)**.
- When an analyst opens the chat drawer, `POST` to `/api/chat/inquire` with the question and active transaction context to display the AI Copilot's answers.

---

## 📋 6. Summary for AI Assistants
See [docs/chatbot_pipeline.md](../docs/chatbot_pipeline.md) and [docs/ml_pipeline.md](../docs/ml_pipeline.md) for full pipeline specifications, prompt architecture, and integration standards.
