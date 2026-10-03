# AI COPY-AND-PASTE INTEGRATION PROMPT & SPECIFICATION

> **INSTRUCTIONS FOR USER:**
> 1. Copy the `ai_models_and_chatbot/` folder into your new project.
> 2. Copy the prompt in **Box 1** below and paste it into your AI assistant (ChatGPT, Claude, Gemini, Cursor, or GitHub Copilot).
> 3. Provide your frontend stack (e.g. React, Next.js, HTML/JS) and backend stack (e.g. FastAPI, Express, Django).
> 4. The AI will immediately write the exact integration code, connecting the ML model and Gemini chatbot into your new app!

---

## 📋 BOX 1: Copy-Paste Prompt for Your AI Assistant

```markdown
I have copied the `ai_models_and_chatbot` folder into my project.
This folder contains:
1. A trained XGBoost transaction fraud risk model (`models/risk_model.pkl`).
2. An AI Gemini/Local forensic chatbot assistant (`chatbot/chat_runner.py`).
3. Sample transaction and customer data (`data/sample_transactions.csv`).

My New Project Stack:
- Backend: [Specify: e.g. FastAPI / Flask / Express (Node.js) / Django]
- Frontend: [Specify: e.g. React / Next.js / Vue / Vanilla HTML+JS]

Read the integration specifications below and generate:
1. The backend API routes to:
   - Run risk prediction on a transaction (`predict_risk`).
   - Query the Gemini/Local forensic chatbot (`ask_chatbot`).
   - Load sample benchmark transactions (`load_sample_transactions`).
2. The frontend integration code / UI component to:
   - Display the transaction risk score badge (0-100) and action directive (CONTINUE / 2FA / HUMAN_REVIEW).
   - Render an interactive AI forensic investigation chat drawer where the user can ask questions about the active transaction.

Here is the exact technical specification of `ai_models_and_chatbot`:
```

---

## ⚙️ BOX 2: Technical Specifications for the AI

### 1. Model Function: `predict_risk(transaction_data)`
Located at: `ai_models_and_chatbot/models/model_runner.py`
Exposed at top level: `from ai_models_and_chatbot import predict_risk`

#### Input Schema (Dictionary):
```python
{
    "amount": float,                  # Required (e.g. 35000.0)
    "amount_deviation": float,        # Optional, default 1.0 (ratio of amount to customer average)
    "is_new_device": int,             # Optional, default 0 (1 if unverified hardware)
    "is_new_receiver": int,           # Optional, default 0 (1 if first-time beneficiary)
    "location_changed": int,          # Optional, default 0 (1 if city changed)
    "hour": int,                      # Optional, default 14 (0-23)
    "day_of_week": int,               # Optional, default 3 (0=Mon, 6=Sun)
    "transactions_last_1h": int,      # Optional, default 1
    "transactions_last_24h": int,     # Optional, default 4
    "failed_attempts": int,           # Optional, default 0
    "account_age_days": int,          # Optional, default 730
    "receiver_transaction_count": int # Optional, default 25
}
```

#### Output Schema (Dictionary):
```python
{
    "risk_score": 93.45,                 # float: 0.0 to 100.0
    "risk_probability": 0.9345,          # float: 0.0000 to 1.0000
    "risk_level": "HIGH",                # "LOW" | "MEDIUM" | "HIGH"
    "recommended_action": "HUMAN_REVIEW", # "CONTINUE" | "ADDITIONAL_REVIEW" | "HUMAN_REVIEW"
    "anomaly_score": 0.725,              # float: 0.0 to 1.0
    "features_used": {...},              # 12 features evaluated
    "model_version": "upay-ai-shield-v1.0.0"
}
```

#### Action Directive Rules:
- `CONTINUE`: Risk < 50.0. Safe transaction. Execute transfer immediately.
- `ADDITIONAL_REVIEW`: Risk 50.0 - 79.9. Moderate deviation. Trigger Step-Up 2FA (SMS OTP).
- `HUMAN_REVIEW`: Risk $\ge$ 80.0. Critical risk / ATO indicator. Hold transfer & route to compliance analyst review queue.

---

### 2. Chatbot Function: `ask_chatbot(message, transaction_context)`
Located at: `ai_models_and_chatbot/chatbot/chat_runner.py`
Exposed at top level: `from ai_models_and_chatbot import ask_chatbot`

#### Input Schema:
```python
message = "Why was this transaction flagged as high risk?"
transaction_context = {
    "transaction_id": "TX10992",
    "amount": 42000.0,
    "amount_deviation": 8.5,
    "is_new_device": 1,
    "is_new_receiver": 1,
    "failed_attempts": 2,
    "hour": 2,
    "risk_score": 93.45,
    "risk_level": "HIGH"
}
```

#### Output Schema (Dictionary):
```python
{
    "response": "Detailed markdown explanation of the findings, ATO indicators, and verification checklist.",
    "engine_used": "gemini-api" | "local-intelligence-engine",
    "status": "success"
}
```

*Note:* If `GEMINI_API_KEY` environment variable is set, it calls the Google Gemini API. If not set, it seamlessly calls the offline local intelligence engine without failing or crashing.

---

### 3. Data Helpers
Located at: `ai_models_and_chatbot/data/data_loader.py`
Exposed at top level: `from ai_models_and_chatbot import load_sample_transactions, load_sample_customers`

- `load_sample_transactions()`: Returns list of 55 pre-computed sample transactions with labels (`LOW`, `MEDIUM`, `HIGH`).
- `load_sample_customers()`: Returns list of 25 customer baselines.

---

## 🛠️ BOX 3: Reference Implementation Templates

### Backend Reference (FastAPI):
```python
from fastapi import FastAPI, HTTPException
from ai_models_and_chatbot import (
    predict_risk,
    ask_chatbot,
    load_sample_transactions
)

app = FastAPI(title="AI Shield Microservice")

@app.get("/api/transactions/sample")
def get_samples():
    """Returns sample benchmark transactions to populate the UI."""
    return load_sample_transactions()

@app.post("/api/risk/evaluate")
def evaluate_transaction(payload: dict):
    """Evaluates transaction risk using trained XGBoost model."""
    return predict_risk(payload)

@app.post("/api/chat/inquire")
def chat_with_ai(payload: dict):
    """Answers analyst questions using Gemini or local forensic assistant."""
    msg = payload.get("message", "")
    context = payload.get("transaction", {})
    return ask_chatbot(message=msg, transaction_context=context)
```

### Frontend Reference (JavaScript / Fetch):
```javascript
// 1. Evaluate Risk
async function checkRisk(transactionData) {
  const res = await fetch("/api/risk/evaluate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(transactionData)
  });
  const data = await res.json();
  console.log(`Risk: ${data.risk_score}/100 (${data.risk_level}) -> ${data.recommended_action}`);
  return data;
}

// 2. Chat with Gemini / AI Assistant
async function askAI(question, activeTransaction) {
  const res = await fetch("/api/chat/inquire", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message: question,
      transaction: activeTransaction
    })
  });
  const data = await res.json();
  return data.response; // Markdown formatted response
}
```
