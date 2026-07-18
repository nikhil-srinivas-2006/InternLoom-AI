
---

# InternLoom-AI: Enterprise Resume Shortlisting Engine

An end-to-end AI-powered recruitment pipeline designed to parse unstructured resume documents from cloud directories, normalize multi-format academic data, resolve conflicting profile signals, and automatically match candidates against multiple concurrent Job Descriptions (JDs) with strict slot awareness.

---

## 🚀 Key Features & Architectural Framework

* **Zero-Preprocessing Pipeline:** Accepts a public Google Drive folder URL or local data directory directly, downloading and sorting raw files automatically.
* **Format-Agnostic Processing:** Robust parsing layer capable of processing `.pdf`, `.docx`, and `.txt` applications seamlessly.
* **Grade Normalisation Engine:** A deterministic matching utility that harmonizes Indian academic performance scales (10-point CGPA, 4-point GPA, percentages) into a unified 10-point metric while executing safety caps on ambiguous values.
* **Advanced Semantic Matching:** Leverages `llama-3.3-70b-versatile` via Groq to evaluate resumes using Exact, Synonym, Partial, and Implicit skill extraction across entire document text bodies.
* **Signal Conflict Resolution:** Systematically balances strong academic/weak practical signals (e.g., high CGPA, zero projects) and weak academic/strong practical profiles.
* **Slot-Aware Multi-JD Allocation:** Automatically runs a single-pass extraction step per candidate and dynamically cross-evaluates them across all active Job Descriptions, strictly partitioning outputs into Headcount Shortlists, Reserve lists, and Human Review allocations.

---

## 🛠️ The Toolkit (Architecture Decisions)

### Tricky Part 1: PDF Layout Chaos & Mixed Media

Instead of relying on rigid bounding boxes or simple regex matching, the engine separates raw textual extraction from contextual structuring. Text is read directly via PyMuPDF (`fitz`), `python-docx`, or standard text streams, and passed into a large context window LLM utilizing strict Pydantic schemas for deterministic structuring.

### Tricky Part 2: Grade Normalisation & Ambiguity Handling

To achieve mathematically perfect evaluation, the engine handles grades outside the LLM layer using a custom Python script.

* **Percentages:** Divided by `9.5` .
* **4-Point Scale:** Multiplied by `2.5` .
* **10-Point Scale:** Passed through as-is.
* **Ambiguity Safeguard:** If a raw grade string lacks context (e.g., just "8.2"), the engine flags the data with a `cgpa_assumption` property, flags the profile as **Low Confidence**, and forces an automatic evaluation score cap of **40 points max** to mitigate risk.

### Tricky Part 3: Skill Extraction from Unstructured Text

The pipeline rejects strict keyword matches or isolated section parsing. The system prompt forces a comprehensive analysis of the document's body, capturing inline technology stacks from project and experience descriptions (e.g., extracting MongoDB, Express, React, and Node.js automatically if a candidate simply states they built a "MERN stack application").

### Tricky Part 4: Parse Quality Affects Score Confidence

If a candidate's profile is missing critical elements (e.g., skills, verified education data), the pipeline labels the record as a **Partial Parse**. During Stage 2 scoring, the evaluation engine flags this status and enforces a strict mathematical cap of **50 points max**, ensuring incomplete profiles never outrank complete, transparent medium-tier profiles. If extraction completely fails, the profile is pushed to a dedicated human review bucket with an explicit warning label.

---

## 📂 Project Structure

```text
InternLoom-AI/
├── data/
│   ├── dummy_resumes/            # Local test resume storage
│   └── job_descriptions/         # Target Job Description JSON matrices
├── documents/
│   ├── parse_quality_report.csv  # Auto-generated parser audit trail
│   └── design_decisions.md       # Full judge compliance documentation
├── output/
│   └── sample_output.json        # Compiled multi-JD matching matrix
├── src/
│   ├── extractor/
│   │   ├── engine.py             # LLM extraction & schema mapping logic
│   │   └── parsers.py            # PDF/DOCX/TXT raw file extraction router
│   ├── matcher/
│   │   └── evaluator.py          # Dual-signal scoring engine & conflict resolver
│   ├── schemas/
│   │   └── resume_schema.py      # Pydantic structured candidate templates
│   ├── utils/
│   │   └── helpers.py            # Grade normalisation utility
│   └── cli.py                    # Main pipeline coordinator orchestration
├── .env                          # Local credentials management
├── requirements.txt              # Pipeline Python configurations
└── README.md                     # System documentation

```

---

## 💻 Quick Start & Setup

### 1. Clone & Initialize the Environment

Ensure your terminal environment is running on Python 3.10+.

```bash
git clone https://github.com/nikhil-srinivas-2006/InternLoom-AI.git
cd InternLoom-AI
python -m venv venv
source venv/Scripts/activate  # On Windows use: venv\Scripts\activate
pip install -r requirements.txt

```

### 2. Configure Environment Variables

Create a `.env` file in the root directory and add your Groq API credentials:

```text
GROQ_API_KEY="gsk_your_actual_groq_api_key_here"

```

### 3. Run the Evaluation Engine

**Evaluating via Local Test Data Directory:**

```bash
python src/cli.py --data_source data/dummy_resumes --jds_dir data/job_descriptions

```

---

## 📊 Pipeline Deliverables & Analytics

Upon execution completion, the application yields two production-grade output files:

1. **`documents/parse_quality_report.csv`**
An immutable audit logs sheet highlighting every candidate file processed, their status (`Clean`, `Partial`, or `Failed`), and exact fields missing for transparent validation tracking.
2. **`output/sample_output.json`**
A highly organized master database structured cleanly by job role. It automatically ranks sorted shortlists within available headcount slots, pushes out-slotted talent into a high-visibility `reserve` queue with their corresponding scores, and houses complete parse anomalies in `human_review_required`.