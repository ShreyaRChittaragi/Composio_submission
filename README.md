# 🚀 Composio AI Product Ops Research Agent

> **An evidence-aware agentic research pipeline that analyzes 100 apps, validates Composio's existing toolkit coverage, identifies integration opportunities, and turns the findings into a reviewer-ready case study.**

Built for the **Composio AI Product Ops Intern Take-Home Assignment**.

---

## 🎯 The Challenge

Composio turns applications into tools that AI agents can call.

Before building a toolkit, we need to answer questions like:

🔐 **How does the app authenticate?**
🔓 **Can developers get credentials themselves?**
🌐 **How mature is the API?**
🤖 **Does an official/native MCP already exist?**
🧩 **Does Composio already support it?**
⚡ **Could we build an agent toolkit today?**

Doing this manually across **100 apps and 10 categories** does not scale.

So I built an agentic research pipeline to do it.

---

# 📊 Final Snapshot

The pipeline analyzed:

| Metric                           |  Result |
| -------------------------------- | ------: |
| 🔎 Apps researched               | **100** |
| 🗂️ Categories                   |  **10** |
| 🧩 Existing Composio toolkits    |  **57** |
| 🚧 Toolkit gaps                  |  **42** |
| ⚠️ Unresolved product match      |   **1** |
| ⚡ Buildable now                  |  **73** |
| 🔐 Buildable with constraints    |  **14** |
| 🌱 Self-serve developer access   |  **78** |
| 🎯 High-confidence records       |  **81** |
| 💡 Top integration opportunities |  **23** |

### 🧩 Composio Coverage

```text
████████████████████████████░░░░░░░░░░░░░░░░░░░░

57  Existing Toolkits
42  Toolkit Gaps
 1  Unresolved
```

The goal wasn't simply finding gaps.

The more useful question was:

> **Which gaps are actually worth building?**

---

# 💡 Key Finding

Not every missing toolkit is an opportunity.

Some applications have:

* 🚫 gated APIs
* 💰 paid-only developer access
* 🏢 partnership requirements
* 📚 incomplete public documentation
* 🔒 restricted authentication
* 🤖 existing native MCP solutions

So the pipeline separates applications into practical opportunity buckets rather than treating every missing integration equally.

### Opportunity Funnel

```text
100 Apps
   │
   ▼
57 Already Covered by Composio
   │
   ▼
42 Toolkit Gaps + 1 Unresolved
   │
   ▼
Access + API + Auth + MCP Analysis
   │
   ▼
23 High-Value Opportunities 🚀
```

---

# 🤖 What I Built

The project is not just a dataset.

It's a multi-stage research and verification pipeline.

```text
                     📱 100 Apps
                          │
                          ▼
                🤖 Research Agent
                          │
          ┌───────────────┼───────────────┐
          ▼               ▼               ▼
       🔐 Auth          🌐 API         🔓 Access
          │               │               │
          └───────────────┼───────────────┘
                          ▼
                    🧠 LLM Analysis
                          │
                          ▼
                  📦 Structured JSON
                          │
                          ▼
             🧩 Composio Catalog Check
                          │
                          ▼
                🔍 Product Validation
                          │
                          ▼
                 🔄 Targeted Retry
                          │
                          ▼
                   🛡️ Final QA
                          │
                          ▼
                👩‍💻 Human Verification
                          │
                          ▼
                  📊 Pattern Analysis
                          │
                          ▼
                 🌐 HTML Case Study
```

---

# 🔬 What the Agent Researches

For every application, the pipeline captures:

| Field                | Question                                          |
| -------------------- | ------------------------------------------------- |
| 🏷️ Category         | What kind of product is this?                     |
| 📝 Description       | What does it do?                                  |
| 🔐 Authentication    | OAuth2, API key, token, Basic, etc.?              |
| 🔓 Developer Access  | Self-serve, paid, admin-gated, partnership-gated? |
| 🌐 API Type          | REST, GraphQL, SDK, CLI, etc.?                    |
| 📚 API Breadth       | Broad or limited surface?                         |
| 🤖 Native MCP        | Official, community, none, or unverified?         |
| 🧩 Composio Coverage | Existing toolkit, gap, or unresolved?             |
| ⚡ Buildability       | Can an agent toolkit be built today?              |
| 🚧 Blocker           | What prevents integration?                        |
| 📈 Confidence        | How trustworthy is the result?                    |
| 🔗 Evidence          | What source supports the claim?                   |

---

# 🧩 Composio Toolkit Validation

One of the most important discoveries was that:

> **Finding a similarly named toolkit does not mean you've found the correct product.**

Early matching produced false positives.

For example:

```text
Squarespace ❌ Square
Zoho Cliq  ❌ Zoho CRM
TranscriptAPI ❌ YouTube
```

Those are related by words, not by product identity. Computers remain courageously literal. 😭

So I added **product-level validation**.

### 📈 Coverage Evolution

```text
Initial detection
       │
       ▼
       0
       │
       ▼
Static correction
       │
       ▼
      23
       │
       ▼
Dynamic catalog discovery
       │
       ▼
      61
       │
       ▼
Product-level validation
       │
       ▼
      57 ✅
```

Final defensible result:

> 🧩 **57 existing toolkits**
> 🚧 **42 toolkit gaps**
> ⚠️ **1 unresolved**

The decreasing number from **61 → 57** is intentional.

The validation layer found false positives and removed them.

---

# 🔄 Verification Philosophy

The research agent is treated as:

> **a first-pass researcher, not ground truth.**

Instead of assuming the model is correct, the pipeline progressively checks its work.

```text
🤖 Agent Research
       ↓
🔗 Evidence Collection
       ↓
🧩 Composio Catalog Validation
       ↓
🔍 Product Identity Validation
       ↓
🔄 Targeted Re-Research
       ↓
🛡️ Automated QA
       ↓
👩‍💻 Human Verification
```

Three principles guide the pipeline:

### 🔎 1. Evidence Over Assumption

A plausible answer isn't automatically considered verified.

### ⚠️ 2. Preserve Uncertainty

If reliable evidence isn't available:

```text
unknown > invented certainty
```

The system keeps the result unresolved or unverified.

### 🛡️ 3. Verify the Agent

Agent outputs are checked through catalog validation, evidence checks, targeted retries, QA rules, and human sampling.

---

# 🛡️ Automated QA

The final QA layer distinguishes between two kinds of problems.

### 🔴 Hard Failures

These block the pipeline:

* Incorrect number of apps
* Duplicate applications
* Broken Composio coverage invariant
* Invalid confidence values
* Invalid classification values
* Structural dataset corruption

### 🟡 Soft Warnings

These don't corrupt the dataset but indicate claims needing stronger evidence:

* Missing evidence URLs
* Native MCP claims without stored official-source evidence
* Incomplete verification coverage

Current structural QA:

```text
Apps:       100
Unique:     100

Composio:
Existing:    57
Gaps:        42
Unresolved:   1

Hard Errors:  0

QA: PASS WITH WARNINGS ✅
```

---

# 👩‍💻 Human Verification

The pipeline can generate a stratified sample for manual checking:

```bash
python final_verify.py sample --sample 20
```

This creates:

```text
data/verification.csv
```

The sample covers different:

* 📂 categories
* 📈 confidence levels
* 🧩 Composio statuses
* ⚡ buildability classifications

After manual verification:

```bash
python final_verify.py accuracy
```

Accuracy is only reported when actual human checks exist.

If:

```text
checked = 0
```

then:

```text
accuracy = not measured
```

No imaginary 97.8% accuracy appearing from the sacred lands of `random.randint()`. 🫠

---

# 🗂️ Repository Structure

```text
composio-ai-product-ops/
│
├── 📄 README.md
├── 📦 requirements.txt
├── 📋 apps.csv
├── 🌐 index.html
│
├── 🤖 research_agent.py
├── 🔄 targeted_research.py
├── 🛡️ final_verify.py
├── 🎨 generate_final_html.py
│
└── 📁 data/
    ├── results.json
    ├── verification.csv
    ├── accuracy.json
    └── qa_report.json
```

---

# ⚙️ Running the Project

## 1️⃣ Clone the repository

```bash
git clone <YOUR_REPOSITORY_URL>
cd composio-ai-product-ops
```

---

## 2️⃣ Create a virtual environment

```bash
python -m venv .venv
```

### Windows

```bash
.venv\Scripts\activate
```

### macOS / Linux

```bash
source .venv/bin/activate
```

---

## 3️⃣ Install dependencies

```bash
pip install -r requirements.txt
```

---

## 4️⃣ Configure Environment Variables

Create:

```text
.env
```

Add the API credentials required by the research pipeline.

⚠️ **Never commit `.env` or API keys to GitHub.**

---

## 5️⃣ Run the Research Agent

```bash
python research_agent.py
```

This performs the initial research across the application dataset.

---

## 6️⃣ Run Targeted Research

Instead of unnecessarily researching all 100 applications again:

```bash
python targeted_research.py
```

This focuses additional research on incomplete or uncertain records.

---

## 7️⃣ Run Final QA

```bash
python final_verify.py qa
```

This validates:

```text
✓ Dataset integrity
✓ 100-app invariant
✓ Duplicate detection
✓ Composio coverage
✓ Confidence ranges
✓ Classification consistency
✓ Evidence availability
```

---

## 8️⃣ Generate Human Verification Sample

```bash
python final_verify.py sample --sample 20
```

After manually verifying the sample:

```bash
python final_verify.py accuracy
```

---

## 9️⃣ Generate the Case Study

```bash
python generate_final_html.py
```

Output:

```text
index.html
```

Open it directly in a browser.

---

# 📂 Data Flow

```text
apps.csv
   │
   ▼
research_agent.py
   │
   ▼
data/results.json
   │
   ├──────────────► targeted_research.py
   │                        │
   │                        ▼
   │                 improved results
   │
   ▼
final_verify.py
   │
   ├──► verification.csv
   ├──► accuracy.json
   └──► qa_report.json
   │
   ▼
generate_final_html.py
   │
   ▼
🌐 index.html
```

---

# 🛠️ Tech Stack

### 🐍 Research Pipeline

* Python
* Structured JSON
* HTTP/API documentation discovery

### 🧠 AI

* Groq
* Llama 3.3
* LLM-assisted extraction and classification

### 🧩 Integration Research

* Composio toolkit catalog
* Official developer documentation
* API/authentication documentation

### 🛡️ Reliability

* Confidence scoring
* Evidence tracking
* Targeted retry pipeline
* Product-level matching
* Automated QA
* Human verification framework

### 🎨 Case Study

* HTML
* CSS
* JavaScript
* Interactive filtering
* Responsive layout

---

# ⚠️ Limitations

No research agent gets magical omniscience privileges.

Some limitations remain:

🔐 Certain APIs require paid accounts or admin access.
🤝 Some developer programs require partnerships or approval.
📚 Documentation can change over time.
🤖 Native MCP availability evolves quickly.
🔍 Similar product names can create matching ambiguity.
👩‍💻 Some claims still benefit from manual verification.

These uncertainties are preserved rather than hidden.

---

# 🚀 Final Deliverables

### 🌐 Interactive Case Study

```text
index.html
```

Contains:

* Executive findings
* Opportunity analysis
* Full 100-app dataset
* Research workflow
* Verification methodology
* Composio coverage analysis

### 🤖 Research Agent

```text
research_agent.py
```

Automates application research.

### 🔄 Targeted Research

```text
targeted_research.py
```

Improves uncertain records without rerunning everything.

### 🛡️ Verification Pipeline

```text
final_verify.py
```

Performs QA and supports human verification.

### 📊 Structured Dataset

```text
data/results.json
```

Contains the final research output for all 100 applications.

---

# 💭 Core Takeaway

The interesting part of this assignment wasn't:

> *“Can an LLM research 100 apps?”*

It was:

> **“Can we build a system that researches 100 apps, recognizes when its own results may be unreliable, verifies those results, and converts them into useful product decisions?”**

That's what this pipeline was designed to explore.

---

## 👩‍💻 Author

**Shreya R Chittaragi**
AI & ML Engineer

Built for the **Composio AI Product Ops Intern Take-Home Assignment** 🚀
