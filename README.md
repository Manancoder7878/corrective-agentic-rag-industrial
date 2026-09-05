# Corrective Agentic RAG for Industrial Diagnostics

An autonomous diagnostic assistant for industrial robotics that ingests official maintenance documentation (ABB IRC5 Controller), performs hybrid dense/sparse retrieval using Qdrant, and executes self-corrective LangGraph loops to guarantee zero-hallucination troubleshooting.

---

## The Problem & Motivation

In high-throughput manufacturing, unscheduled robotic downtime costs thousands of dollars per minute. When an industrial controller (such as the ABB IRC5) triggers a fault, maintenance technicians face two major failure modes with existing approaches:

1. **Manual Diagnostic Overhead:** Technicians must manually navigate dense, 600+ page technical manuals to cross-reference multi-digit error event logs (e.g., `38001`, `10012`) with electrical schematics and symptom trees.
2. **The Failure of Naive GenAI/RAG:** Standard RAG pipelines fail in industrial contexts:
   * **Semantic blindness:** Pure vector search frequently misses exact alphanumeric codes, serial numbers, and specific error IDs.
   * **Hallucination risk:** Standard LLMs will guess torque specifications, pin configurations, or safety clearance steps when context is weak, creating catastrophic safety and equipment hazards.
   * **Static query failure:** If the initial operator input is vague (e.g., *"robot arm shakes on axis 2"*), a naive system retrieves irrelevant passages and produces ungrounded advice.

### The Solution: Corrective Agentic RAG
This system treats retrieval as an active, self-correcting decision loop:
* **Hybrid Retrieval (Dense + BM25):** Ensures exact numerical event codes and broad physical symptoms are indexed and retrieved with equal precision.
* **Deterministic Self-Correction:** An active LangGraph evaluation node grades retrieved passages before generation. If the context is missing or irrelevant, the query is autonomously rewritten or flagged.
* **Strict Source Attribution:** Diagnostic steps are strictly constrained to cited manual sections, guaranteeing auditable, safety-compliant maintenance guidance.

---

## Architectural Workflow


```

Operator Fault Query (e.g., "FlexPendant black screen" or "Event 38001 SMB battery")
│
▼
[ Query Reformulator & Normalizer ]
│
▼
[ Hybrid Retriever: Qdrant Dense (Semantic) + Sparse (BM25 Token Matching) ]
│
▼
[ Document Grader Node ] ──> Are chunks relevant to the exact fault code / symptom?
│
├── NO  ──> [ Query Rewrite Loop ] (Max 2 retries)
│
└── YES ──> [ Grounded Generator Node ]
│
▼
[ Hallucination & Citation Checker ]
│
├── Hallucination detected ──> Regenerate with strict grounded prompt
└── Grounded ──> Final Diagnostic Steps with Exact Manual Citations

```

---

## Target Corpus & Domain

* **Target System:** ABB IRC5 Robot Controller (M2004)
* **Reference Documentation:** *Operating manual - Troubleshooting, IRC5* (Document ID: `3HAC020738-001`)
* **Target Scenarios:**
  * Exact alphanumeric fault code recovery (e.g., Event `10012: Safety guard stop`, Event `38001: Battery backup lost`).
  * Symptom-level diagnostics (e.g., controller boot failure, FlexPendant communication drop, motor contactor faults).
  * Verifiable safety instructions and hardware replacement sequences with exact manual page citations.

---

## Repository Structure

```text
corrective-agentic-rag-industrial/
├── data/
│   ├── manuals/                      # Source PDFs (ABB IRC5 3HAC020738-001)
│   └── qdrant_data/                  # Persistent local Qdrant storage
├── docs/                             # Engineering benchmarks & specs
├── src/
│   ├── agent/                        # LangGraph orchestration, state & nodes
│   ├── ingestion/                    # Metadata-aware PDF extraction & chunking
│   └── retrieval/                    # Qdrant hybrid retrieval engine
├── tests/                            # Automated pytest validation suite
├── requirements.txt
└── README.md

```

---

## Development Setup

### 1. Prerequisites

* Python 3.10+
* Virtual Environment (`venv`)

### 2. Installation

```bash
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd corrective-agentic-rag-industrial
pip install -r requirements.txt

```