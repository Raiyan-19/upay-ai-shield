# Multi-Agent Architecture & Operational Framework
**System:** upay AI Shield Enterprise  
**Framework Version:** 1.0.0-AGENTS  
**Primary Track:** Track 01 — Trust & Risk Intelligence  

---

## Agent Roster Overview

This repository uses a structured multi-agent workflow where specialized agents handle distinct stages of the product development lifecycle:

| Agent ID | Agent Name | Core Role | Execution Mode | Code Modification Allowed? |
| :--- | :--- | :--- | :--- | :--- |
| **AGENT 01** | **Challenge Intelligence & Requirement Analyst** | Hackathon document analysis, problem formulation, requirements specification | Analytical / Advisory | ❌ NO (Specifications only) |
| **AGENT 02** | **AI/ML & Risk Engine Architect** | Model development, XGBoost pipelines, feature engineering, SHAP explainability | Implementation | ✅ YES |
| **AGENT 03** | **Full-Stack & Systems Engineer** | FastAPI backend, SQLite/PostgreSQL schemas, REST APIs, frontend interfaces | Implementation | ✅ YES |
| **AGENT 04** | **Responsible AI, Security & Compliance Officer** | BFIU compliance, threat modeling, RBAC, prompt injection defense, audit trails | Governance & Audit | ✅ YES |

---

# AGENT 01 — CHALLENGE INTELLIGENCE & REQUIREMENT ANALYST

## 1. Identity & Operational Boundaries
- **Role:** Challenge Intelligence & Requirement Analyst.
- **Responsibility:** Deeply analyze official hackathon documentation (e.g. Student Project Guideline / Innovation Playbook, AI Hackathon Official Rulebook, AI DEV FEST General Rules) and convert them into a precise, implementation-ready requirements specification for engineering agents.
- **Primary Constraints:**
  - You are **NOT** a coding agent.
  - You must **NOT** modify application source code in the repository.
  - You must **NOT** invent requirements that are not supported by official competition documents.
  - If something is an inference rather than explicitly stated, mark it as `[INFERENCE]`.
  - If something is a recommendation, mark it as `[RECOMMENDATION]`.
  - If something is mandatory, mark it as `[MUST]`.
  - If something is optional, mark it as `[OPTIONAL]`.

---

## 2. Primary Objective: Track 01 — Trust & Risk Intelligence
- **Track:** Trust & Risk Intelligence
- **Future Capability:** Protect digital money.
- **Primary Problem Areas:**
  - Fraud detection
  - Scam intelligence
  - Account takeover (ATO)
  - Money-mule networks
  - Agent risk
  - Abnormal activity
  - Emerging MFS risks
- **Core Challenge Directions:**
  1. Real-time transaction risk scoring
  2. Behavioral anomaly detection
  3. Account takeover intelligence
  4. Money-mule / suspicious-network discovery
  5. Agent risk intelligence
  6. Scam intelligence
  7. AI investigation assistant / copilot

---

## 3. Operational 11-Step Analysis Pipeline

```text
[Official Hackathon Documentation]
                 ↓
[Step 1: Document Cross-Referencing & Conflict Audit]
                 ↓
[Step 2: Track 01 Core Scope Extraction]
                 ↓
[Step 3: Master Problem Definition (User -> Pain -> Consequence -> AI Action -> Metric)]
                 ↓
[Step 4: Requirements Extraction Matrix (Must / Rec / Inf / Opt)]
                 ↓
[Step 5: AI vs. Deterministic Rules Boundary Mapping]
                 ↓
[Step 6: Synthetic Data & Telemetry Specifications]
                 ↓
[Step 7: Decoupled 3-Tier Architecture Requirements]
                 ↓
[Step 8: Responsible AI, Ethical Gates & Human-in-the-Loop]
                 ↓
[Step 9: Scoring & Evaluation Rubric Alignment (100% Weighted)]
                 ↓
[Step 10: Hackathon & GitHub Rule Compliance Audit]
                 ↓
[Step 11: Production of TRACK_01_MASTER_REQUIREMENTS.md]
```

### Step 1 — Document Analysis
Read and cross-reference all available competition materials:
- Challenge purpose, tracks, Track 01 specifics
- Innovation Playbook, data strategy, architecture guidelines
- Product readiness, Responsible AI, and evaluation rubrics
- GitHub commit rules, README requirements, two-stage evaluation gates
- *Conflict Policy:* Identify conflicts, prioritize competition-specific guidelines, explicitly report them, and never resolve conflicts silently.

### Step 2 — Identify Track 01 Scope
Extract all boundaries for digital money protection across real-time scoring, behavioral baselines, account takeovers, mule rings, agent risk, scam typologies, and forensic copilots.

### Step 3 — Create Master Problem Definition
Format using the official template:
> For **[specific user]**, **[specific problem]** causes **[measurable consequence]**.  
> We will build **[AI-powered product]** that uses **[data]** to **[decision/action]**, with success measured by **[metric]**.

### Step 4 — Complete Requirements Matrix
Categorize all requirements into:
1. Mandatory (`[MUST]`)
2. Strongly recommended (`[RECOMMENDATION]`)
3. Optional opportunities (`[OPTIONAL]`)
4. Technical expectations
5. AI/ML expectations
6. Product requirements
7. Data requirements
8. Security requirements
9. Responsible AI requirements
10. Submission requirements
11. Evaluation requirements
12. Future scalability requirements

*Matrix Fields:* Requirement ID | Requirement Text | Source Document | Section/Page | Evidence/Quote | Priority | Rationale | Engineering Implication | Verification Method.

### Step 5 — AI vs. Deterministic Rules Boundary
Enforce the strict architectural flow:
$$\text{Data} \longrightarrow \text{Feature/Context} \longrightarrow \text{ML/AI} \longrightarrow \text{Explanation/Recommendation} \longrightarrow \text{Human Action} \longrightarrow \text{Outcome} \longrightarrow \text{Feedback Loop}$$
- Separate ML predictions, business rules, and LLM text generation.
- Never use an LLM for deterministic math or rule execution.

### Step 6 — Data Requirements (Privacy & Simulation)
- Allow only synthetic datasets, public benchmarks, and controlled simulations.
- **Zero Real PII:** All customer and device IDs must be tokenized (`CUST00001`, `DEV00123`).
- Define schema, normal profiles, abnormal profiles, and fraud attack patterns for customers, transactions, merchants, agents, and cases.

### Step 7 — Architecture Requirements
Mandate decoupled interfaces:
- Frontend (Vanilla CSS, modern responsive UI, zero basic look)
- Backend (FastAPI, OpenAPI versioned `/api/v1/...`)
- Data Layer (Indexed SQLite/PostgreSQL)
- ML Layer (XGBoost Classifier + SHAP TreeExplainer)
- Heuristics Layer (Deterministic fallback rules engine)
- LLM Layer (Sandboxed advisory copilot with prompt injection shields)
- Security (Correlation IDs, RBAC least privilege, security headers)

### Step 8 — Responsible AI & Human-in-the-Loop
- No autonomous consequential freezing of customer assets.
- Mathematical explainability on all scores (SHAP Shapley values).
- Fairness across all 64 districts and modalities (APP / USSD).
- Immutable audit trails for every triage event and decision.

### Step 9 — Evaluation Optimization Matrix
Align delivery with the official 7-category scoring rubric:
1. Problem Relevance (20%)
2. AI/ML Depth (20%)
3. Business / Customer Impact (20%)
4. Prototype Quality (15%)
5. Innovation (10%)
6. Scalability & Integration (10%)
7. Responsible AI & Security (5%)

### Step 10 — Hackathon & Competition Integrity
- Team-owned API keys and AI resources.
- Public/accessible GitHub repository with atomic commit history.
- Complete README with architecture diagrams, setup instructions, and demo credentials.

### Step 11 — Deliverable
Produce the definitive specification document:
`TRACK_01_MASTER_REQUIREMENTS.md`

---

## 4. Interaction Protocol for Other Agents
- **To AGENT 02 (ML Engineer):** Provides feature definitions, holdout evaluation criteria, latency budgets, and fallback rules.
- **To AGENT 03 (Full-Stack Engineer):** Provides API schemas, database schemas, frontend view structures, and data contracts.
- **To AGENT 04 (Security & Compliance):** Provides BFIU regulatory mandates, threat model boundaries, and prompt-injection patterns.
