
---

# InternLoom-AI: Architectural & Design Decisions

This document outlines the core architectural choices, fallback strategies, and algorithmic safeguards implemented in the InternLoom Resume Shortlisting Engine to ensure strict adherence to the enterprise grading rubric.

## 1. Zero-Preprocessing & Cloud Ingestion

* **Decision:** Implemented `gdown` for direct Google Drive folder ingestion and temporary environment provisioning.
* **Rationale:** The rubric explicitly forbade manual preprocessing. By parsing the Google Drive URL, creating a temporary `temp_drive_downloads` workspace, and dynamically cleaning it up post-execution, the engine operates 100% autonomously from cloud-hosted raw data without requiring manual file downloads or sorting.

## 2. Format-Agnostic Extraction Layer

* **Decision:** Built a multi-format routing layer using `PyMuPDF` (`fitz`), `python-docx`, and native Python text reading.
* **Rationale:** While the problem statement highlighted PDF layout chaos, real-world hiring pipelines receive mixed file formats. The system dynamically detects `.pdf`, `.docx`, and `.txt` files, ensuring no candidate is silently dropped due to unexpected file extensions or formatting oversights.

## 3. Engine Selection: Groq LPU + Llama 3.3 70B

* **Decision:** Migrated from local computing (Ollama) and the Gemini Free Tier to Groq's cloud LPU running the `llama-3.3-70b-versatile` open-source model.
* **Rationale:**
* *Gemini:* The 20-request daily quota was insufficient for the 300+ matrixed requests required to evaluate a full candidate pool against 5 different Job Descriptions.
* *Local Compute:* Processing complex JSON extraction on a local RTX 4050 GPU created severe VRAM bottlenecks, pushing processing times to over 3 minutes per resume.
* *Groq API:* Provided the necessary speed for high-volume evaluation (sub-second generations) while utilizing a 70B parameter model capable of flawless Pydantic schema mapping without hallucinating JSON structures.



## 4. API Throttling & Fault Tolerance

* **Decision:** Implemented a dual-layered safety net: exponential backoff (60-second sleep cycles on `429` Rate Limit errors) combined with micro-delays between standard requests.
* **Rationale:** Processing 50 resumes against multiple JDs creates a massive burst of concurrent API calls. This throttling ensures the engine stays cleanly under Groq’s 6,000 Tokens-Per-Minute limit. If a quota spike occurs, the system elegantly catches the exception, waits out the penalty, and resumes execution without crashing.

## 5. Grade Normalisation & Risk Mitigation

* **Decision:** Mathematical scaling of 4-point GPAs and percentages to a 10-point CGPA standard, coupled with an active **Ambiguity Cap**.
* **Rationale:** If a candidate provides a raw number (e.g., "8.2") without context, the extraction engine flags a `cgpa_assumption`. The evaluator engine intercepts this flag and mathematically caps the candidate's final evaluation score at **40 points maximum**, ensuring high-risk profiles do not artificially inflate their ranking above verified, transparent talent.

## 6. Parse Integrity & The "Partial Parse" Penalty

* **Decision:** Validating the extracted JSON schema against required fields (Full Name, Skills, Education Details) prior to the evaluation stage.
* **Rationale:** If the AI successfully reads the document but fails to locate critical structural data, the profile is flagged as `Partial`. The scoring engine enforces a strict cap of **50 points maximum** for these profiles, mathematically preventing candidates with broken or obfuscated resumes from occupying primary shortlist slots.

## 7. Strict Slot Awareness & Cross-Evaluation Matrix

* **Decision:** Executing a single-pass extraction step, followed by a multi-pass evaluation loop utilizing strict array slicing tied to the JD's `AVAILABLE_SLOTS` variable.
* **Rationale:** To optimize compute resources, a candidate's file is parsed into structured JSON exactly once. That data object is then evaluated sequentially against every active Job Description in the system. Candidates are sorted by their match score in descending order, and the array is mathematically partitioned: indices matching the available headcount are routed to the `shortlist`, while the overflow is systematically relegated to the `reserve` pool, guaranteeing 100% compliance with corporate headcount limits.