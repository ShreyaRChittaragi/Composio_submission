# Composio AI Product Ops Research Agent

An agentic research pipeline built for the **Composio AI Product Ops Intern take-home assignment**.

The system researches 100 applications across 10 categories, analyzes their developer/API ecosystem, validates existing Composio toolkit coverage, identifies integration opportunities, and generates a self-contained HTML case study.

## Overview

Manually researching 100 applications for authentication, API access, MCP support, developer accessibility, and agent-toolkit buildability is slow and difficult to verify consistently.

This project automates that workflow while preserving evidence and uncertainty.

The pipeline performs:

1. Automated research across the 100 provided applications
2. Authentication and API-surface classification
3. Self-serve vs gated developer-access analysis
4. Native MCP investigation
5. Agent-toolkit buildability assessment
6. Dynamic Composio toolkit coverage checking
7. Product-level validation to remove false-positive toolkit matches
8. Targeted re-research for incomplete or low-confidence records
9. Automated QA and a human-verification framework
10. Pattern and opportunity analysis
11. Generation of a self-contained HTML case study

## Final Dataset

The final dataset contains **100 unique applications**.

### Composio Coverage

| Status                    | Apps |
| ------------------------- | ---: |
| Existing Composio toolkit |   57 |
| Toolkit gap               |   42 |
| Unresolved product match  |    1 |
| Total                     |  100 |

The unresolved case is kept explicitly uncertain rather than forcing a potentially incorrect product match.

## Why Product-Level Validation Matters

Simple string or catalog matching produced false positives.

For example, similarly named products can belong to completely different platforms. The validation stage therefore checks whether a discovered Composio toolkit actually represents the requested product.

The Composio coverage evolved during verification:

```text
Initial detection       → 0
Static correction       → 23
Dynamic catalog search  → 61
Product-level validation→ 57
```

This correction loop is intentional. The pipeline does not assume its first answer is correct.

## Research Fields

Each application is analyzed for:

* Category
* One-line product description
* Authentication methods
* Developer access model
* API type
* API breadth
* Native MCP availability
* Composio toolkit availability
* Agent-toolkit buildability
* Primary blocker
* Confidence
* Supporting evidence

Unknown or insufficiently supported values are preserved as uncertain instead of being silently converted into confident claims.

## Pipeline Architecture

```text
100 Apps
   │
   ▼
Research Agent
   │
   ├── Official documentation discovery
   ├── Authentication research
   ├── API-surface research
   ├── Access/gating research
   └── MCP investigation
   │
   ▼
Structured results.json
   │
   ▼
Composio Catalog Validation
   │
   ├── Dynamic toolkit discovery
   ├── Product matching
   └── False-positive removal
   │
   ▼
Targeted Research
   │
   └── Retry uncertain/incomplete records
   │
   ▼
QA + Verification Framework
   │
   ├── Dataset invariants
   ├── Evidence checks
   ├── Confidence checks
   └── Human verification sample
   │
   ▼
Analysis
   │
   ▼
Self-Contained HTML Case Study
```

## Repository Structure

```text
.
├── README.md
├── requirements.txt
├── apps.csv
├── index.html
│
├── research_agent.py
├── targeted_research.py
├── final_verify.py
├── generate_final_html.py
│
└── data/
    ├── results.json
    ├── verification.csv
    ├── accuracy.json
    └── qa_report.json
```

### Main Files

**`research_agent.py`**

Runs the primary automated research workflow and creates structured application-level research.

**`targeted_research.py`**

Re-researches incomplete or uncertain applications rather than unnecessarily rerunning all 100.

**`final_verify.py`**

Provides the final QA and human-verification workflow.

It distinguishes between:

* **Hard failures:** dataset-integrity problems that should block the pipeline
* **Soft warnings:** incomplete evidence or claims requiring additional verification

**`generate_final_html.py`**

Transforms the final structured dataset and analysis into the self-contained case-study page.

**`index.html`**

Final reviewer-facing case study.

## Running the Project

### 1. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure environment variables

Create a local `.env` file for any API credentials required by the research pipeline.

Do not commit `.env` or API keys to Git.

### 4. Run the research agent

```bash
python research_agent.py
```

For targeted re-research:

```bash
python targeted_research.py
```

The targeted workflow is preferred once the initial dataset exists because it avoids overwriting validated results unnecessarily.

## Verification

Generate a stratified human-verification sample:

```bash
python final_verify.py sample --sample 20
```

This creates:

```text
data/verification.csv
```

After manually checking sampled claims against authoritative documentation, calculate measured accuracy:

```bash
python final_verify.py accuracy
```

Run final QA:

```bash
python final_verify.py qa
```

The QA layer validates dataset integrity, Composio coverage invariants, confidence values, evidence availability, and classification consistency.

At the current snapshot, automated structural QA passes with soft evidence warnings. Manual field-level accuracy should only be reported after the verification sample has actually been completed.

## Generate the Case Study

```bash
python generate_final_html.py
```

This produces:

```text
index.html
```

Open `index.html` directly in a browser to inspect the final case study.

## Research Philosophy

The pipeline follows three principles:

### 1. Evidence over assumption

A plausible answer is not automatically treated as a verified answer.

### 2. Preserve uncertainty

If reliable evidence cannot be found, the system keeps the result unresolved or unverified rather than fabricating certainty.

### 3. Verify the agent

The research agent is treated as a first-pass researcher, not as ground truth.

Automated validation, product-level matching, targeted retries, QA checks, and human sampling are used to progressively improve reliability.

## Key Insight

The useful output is not simply a table of 100 applications.

The pipeline is designed to answer the product question behind the dataset:

> **Where does Composio already have strong coverage, where are the actionable toolkit opportunities, and which apparent opportunities actually require additional access, evidence, or partnership work?**

The final HTML case study presents these patterns alongside the underlying research and methodology.

## Limitations

* Developer documentation and API availability can change over time.
* Some applications require paid accounts, admin approval, or partnership access for complete verification.
* Native MCP classifications without sufficient first-party evidence are reported conservatively.
* Automated research can misclassify similarly named products, which is why product-level validation is included.
* Human verification remains the final reliability layer for claims selected in the verification sample.

## Tech Stack

* Python
* Groq / LLM-assisted research
* Structured JSON research pipeline
* Composio toolkit catalog validation
* HTML/CSS/JavaScript
* Automated QA and verification tooling

## Deliverables

* **Interactive HTML case study:** `index.html`
* **Research dataset:** `data/results.json`
* **Research agent:** `research_agent.py`
* **Verification pipeline:** `final_verify.py`
* **Reproducible source code:** this repository

---

Built as part of the **Composio AI Product Ops Intern take-home assignment**.
