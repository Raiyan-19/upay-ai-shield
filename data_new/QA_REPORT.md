# Upay AI Shield — Dataset Cleaning & QA Report

- Source: `Pasted text(6).txt`
- Original rows: **6,000**
- Clean master rows: **5,416**
- Exact normalized duplicates removed: **584**
- PASS rows: **5,416**
- REVIEW rows: **0**
- Domains: **30**

## Safety checks
- `contains_real_pii=True`: 0
- Live URL pattern found: 0
- Phone-like pattern found: 0
- Numeric OTP/PIN-like pattern found: 0

## Important
This is a synthetic/redacted defensive dataset, not real Upay customer data. The cleaning process does not invent real users, accounts, OTPs, PINs, phone numbers, or working phishing URLs.

## Files
- `clean_master.csv` — cleaned master dataset with QA metadata
- `message_model_ready.csv` — compact NLP training/evaluation dataset
- `removed_duplicates.csv` — rows removed as exact normalized-text duplicates
- `qa_report.json` — machine-readable QA report
