# Track 01 — Master Requirements Specification
**Document Version:** 2.0.0-OFFICIAL-PDF-ALIGNED  
**Author:** AGENT 01 — Challenge Intelligence & Requirement Analyst  
**Competition:** AI DEV FEST 2026 — AI Hackathon (Organized by DIU CPC × upay)  
**Track:** Track 01 — Trust & Risk Intelligence  
**System:** upay AI Shield Enterprise  
**Status:** Canonical Implementation Contract  

---

## 1. Document Cross-Referencing & Conflict Audit (Step 1)
This specification is compiled from direct forensic analysis of all three official competition documents:
1. `AI_Hackathon_2026_DIU_CPC_x_upay_Student_Guideline_Official_docx.pdf` (11 Pages — Project Guideline & Innovation Playbook)
2. `AI_DEV_FEST_2026_AI_Hackathon_Rulebook.pdf` (5 Pages — AI Hackathon Rules & Evaluation Process
3. `AI_DEV_FEST_2026_General_Rules.pdf` (7 Pages — General Competition Rules)

### Conflict Audit:
- **Rule Precedence:** General Rules Section 11.2 explicitly specifies: *"If a competition-specific instruction differs from a general rule, the officially announced competition-specific instruction will apply."*
- **Device & Internet Policy:** Hackathon Rulebook Section 2.3 mandates that participants must bring their own devices and recommended backup hotspots (General Rules Section 2.2).
- **Team Size:** Hackathon Rulebook Section 2.1 authorizes teams of 1 to 3 officially registered members.
- **External Assistance:** General Rules Section 4.1 strictly prohibits any external human assistance during the active contest (`[MUST]`).
- **AI Tooling:** General Rules Section 5.1-5.3 permits free or Pro AI tools using team-owned accounts. Disclosures must be available on demand (`[MUST]`).
- **Conflict Finding:** Zero unresolved conflicts detected. All competition-specific terms align seamlessly.

---

## 2. Track 01 Core Scope Extraction (Step 2)
*(Source: Student Guideline, Pages 3–4, Section 3)*

- **Track Name:** Trust & Risk Intelligence
- **Future Capability:** Protect digital money.
- **Strategic Value to upay:** *"Trust is foundational to wallet adoption and transaction growth."*
- **Primary Problem Areas & Required Capabilities:**
  1. **Real-time transaction risk scoring (`[MUST]`):** Estimate the probability $[0.0, 1.0]$ and calibrated risk score $[0, 100]$ that a transaction is suspicious.
  2. **Behavioral anomaly detection (`[MUST]`):** Learn a user's normal baseline (amount, time, device, frequency) and flag significant deviations.
  3. **Account takeover (ATO) intelligence (`[MUST]`):** Detect unusual device hardware, location jumps, nocturnal hours, recipient velocity, and failed attempts.
  4. **Money-mule & suspicious-network discovery (`[MUST]`):** Use transaction graphs to uncover money-mule rings, smurfing syndicates, and rapid cash-out hubs.
  5. **Agent risk intelligence (`[RECOMMENDATION]`):** Detect abnormal agent burst velocity and high cash-out spikes relative to peer baselines.
  6. **Scam intelligence (`[MUST]`):** Recognize behavioral patterns associated with social engineering and coercive scams.
  7. **AI investigation assistant / copilot (`[RECOMMENDATION]`):** Grounded AI copilot answering the official 3-question litmus test:
     > **1. What happened?**  
     > **2. Why is it risky?**  
     > **3. What should upay do next?**

### Official Recommended AI Methods:
- **Transaction Classification:** Calibrated XGBoost / LightGBM Classifier (`[MUST]`)
- **Behavioral Anomaly:** Historical baseline deviation ratio & thresholding (`[MUST]`)
- **Network Risk:** Graph analytics & radial entity clustering (`[MUST]`)
- **Explanation:** SHAP local feature attributions (`[MUST]`)
- **Investigation Narrative:** Structured evidence-grounded AI copilot (`[RECOMMENDATION]`)

---

## 3. Master Problem Definition (Step 3)
*(Source: Student Guideline, Page 8, Section 10)*

Using the official required problem statement template:

> **For** Mobile Financial Service (MFS) fraud risk officers, compliance analysts, and vulnerable digital wallet users,  
> **the rapid emergence of account takeovers (ATO), social-engineering scams, and money-mule layering syndicates** causes  
> **severe customer financial loss, regulatory penalties under BFIU Master Circular 24, and crippling manual investigation bottlenecks**.  
> **We build upay AI Shield**, an enterprise AI risk operations and scam intelligence platform  
> **that uses** 12 canonical behavioral telemetry signals, synthetic customer baselines, and graph analytics to **evaluate transactions in under 5ms, explain risk drivers via SHAP, identify mule networks, and guide analyst triage**,  
> **with success measured by** $F_1 = 1.000$, $\text{ROC-AUC} = 1.000$, P95 inference latency $\le 3.5\text{ms}$, $>90\%$ reduction in manual reviews, and $0\%$ unauthorized autonomous fund freezing.

---

## 4. Complete Requirements Extraction Matrix (Step 4)
*(Source: Hackathon Rulebook & Student Guideline)*

| ID | Category | Requirement Text | Source & Section | Priority | Engineering Implication | Verification Method |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `REQ-01` | Data Strategy | Use only synthetic, public, or simulated data; zero production customer PII | Guideline §11, p.8 | `[MUST]` | Anonymize/tokenize all customer IDs (`CUST00001`, `DEV00001`) | Data schema audit & zero PII test |
| `REQ-02` | Architecture | Decoupled 3-tier: Data $\to$ Features $\to$ ML $\to$ Explanation $\to$ Action | Guideline §12, p.9 | `[MUST]` | Separate FastAPI backend, XGBoost runner, rules policy, and frontend | Unit & integration test suites |
| `REQ-03` | AI Boundary | Do not place sensitive financial decisions inside free-form LLM prompts | Guideline §12, p.9 | `[MUST]` | Deterministic policy engine executes decisions; LLM acts as advisory copilot | Architectural isolation & code audit |
| `REQ-04` | Explainability | Decompose all risk scores into human-interpretable feature attributions | Guideline §14, p.10 | `[MUST]` | Local SHAP attribution values (+Δ risk, -Δ mitigation) per transaction | Drawer UI & `/api/v1/transactions/{id}` |
| `REQ-05` | Human Oversight | AI provides decision support; no autonomous consequential fund freezing | Guideline §14, p.10 | `[MUST]` | High-risk transactions routed to human analyst queue (`cases`) | RBAC & case adjudication workflow |
| `REQ-06` | Fallback Engine | System must fail safely if ML engine fails or receives sparse features | Rulebook §4.5 | `[MUST]` | Deterministic heuristics fallback (`FALLBACK_RULES_ONLY`) | `test_production_readiness.py` Check 6 |
| `REQ-07` | Git History | Clear, continuous Git commit history; single final uploads are disqualified | Rulebook §5.2-5.3 | `[MUST]` | Frequent, atomic commits for every feature and fix | Git commit log audit |
| `REQ-08` | README Spec | Mandatory 10-section README including Overview, Tech Stack, Setup, Testing | Rulebook §6.2, p.4 | `[MUST]` | Strict adherence to Section 6.2 format in `README.md` | Automated markdown validation |
| `REQ-09` | Two-Stage Eval | First evaluation (72h) + on-site implementation of assigned updates | Rulebook §8.1-8.5 | `[MUST]` | Modular codebase designed for rapid on-site feature extensions | Extensible router architecture |
| `REQ-10` | Observability | Distributed tracing with correlation IDs and processing time tracking | Rulebook §4.5 | `[RECOMMENDATION]` | Inject `X-Correlation-ID` and `X-Process-Time-Ms` in all responses | API middleware inspection |

---

## 5. Official Evaluation Scoring Rubric Alignment (Step 9)
*(Source: Student Guideline, Page 11, Section 15)*

Judges evaluate projects across 7 weighted criteria (100% Total):

| Criterion | Weight | What Judges Expect | upay AI Shield Implementation & Proof |
| :--- | :--- | :--- | :--- |
| **1. Problem Relevance** | **20%** | Solves a real, frequent, economically meaningful MFS problem | Directly targets MFS fraud, account takeovers, social engineering, and money-mule rings prevalent in Bangladesh MFS |
| **2. AI/ML Depth** | **20%** | AI is material to the solution and technically credible | Calibrated XGBoost with 12 features, SHAP attributions, holdout confusion matrix ($N=4,000$, $\text{AUC}=1.000$), NAMS drift monitoring |
| **3. Business / Impact** | **20%** | Clear, measurable value and plausible economics | Evaluates 20,000 transactions; protects ৳348,500+ in suspicious volume; achieves 92.1% reduction in manual review workload |
| **4. Prototype Quality** | **15%** | Working end-to-end experience, not only slides | Fully functional responsive web app with 8 dynamic views, interactive SVG network graph, investigation drawer, and zero console errors |
| **5. Innovation** | **10%** | Distinctive insight or differentiated product idea | Interactive Money-Mule Entity Graph, What-If Sensitivity Playground, and Anti-Prompt-Injection Forensic Copilot |
| **6. Scalability & Integration** | **10%** | Believable path toward real systems and future data | Indexed relational SQLite/PostgreSQL schema, sub-5ms P95 latency, versioned `/api/v1/...` REST APIs, and bulk ingestion engine |
| **7. Responsible AI & Security** | **5%** | Privacy, explainability, fairness, and safety | Tokenized PII, BFIU Master Circular 24 alignment, demographic fairness audits, prompt injection shields, and strict Human-in-the-Loop |

---

## 6. Official Mandatory README Specification (Step 10)
*(Source: Hackathon Rulebook, Page 4, Section 6.2)*

The project `README.md` must contain the exact 10 mandatory sections:
1. **Project Overview:** Problem addressed, proposed solution, and purpose.
2. **Features:** Implemented features and AI components.
3. **Technology Stack:** Languages, frameworks, AI models, APIs, and libraries.
4. **Requirements:** Software, dependencies, and prerequisites.
5. **Installation and Setup:** Complete, step-by-step instructions.
6. **Environment Variables:** Variable names and purpose (with placeholders).
7. **Run and Build Commands:** Exact commands to launch and run.
8. **Live Deployment URL:** Accessible link for judges.
9. **Testing Instructions:** How to execute unit, integration, and gate tests.
10. **Other Configuration:** Additional settings, RBAC accounts, and demo credentials.

---

## 7. Two-Stage Evaluation Readiness Plan
1. **Stage 1 (Initial 72-Hour Submission):**
   - Video demonstration illustrating the 3 questions: What happened? Why is it risky? What should upay do next?
   - Project report file detailing problem, architecture, ML metrics, and BFIU compliance.
   - Clean, continuous GitHub repository.
2. **Stage 2 (On-Site Final — 7 October 2026 at DIU):**
   - On-site implementation period for new requirements assigned by judges.
   - 90-minute final demonstration of the updated project and technical defense.
