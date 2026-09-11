# Corrective Agentic RAG for Industrial Diagnostics

An autonomous diagnostic assistant for industrial robotics that ingests official maintenance documentation (ABB IRC5 Controller), performs hybrid dense/sparse retrieval using Qdrant, and executes self-corrective LangGraph cyclic loops to guarantee zero-hallucination troubleshooting.

---

## The Problem & Motivation

In high-throughput manufacturing, unscheduled robotic downtime costs thousands of dollars per minute. When an industrial controller (such as the ABB IRC5) triggers a fault, maintenance technicians face two major failure modes with existing approaches:

1. **Manual Diagnostic Overhead:** Technicians must manually navigate dense, 450+ page technical manuals to cross-reference multi-digit error event logs (e.g., `38001`, `10012`) with electrical schematics and symptom trees.
2. **The Failure of Naive GenAI/RAG:** Standard RAG pipelines fail in industrial contexts:
   * **Semantic blindness:** Pure vector search frequently misses exact alphanumeric codes, serial numbers, and specific error IDs.
   * **Hallucination risk:** Standard LLMs will guess torque specifications, pin configurations, or safety clearance steps when context is weak, creating catastrophic safety and equipment hazards.
   * **Static query failure:** If the initial operator input is vague (e.g., *"robot arm shakes on axis 2"* or technician slang), a naive system retrieves irrelevant passages and produces ungrounded advice.

### The Solution: Corrective Agentic RAG
This system treats retrieval as an active, self-correcting decision loop:
* **Hybrid Retrieval (Dense + BM25):** Combines BGE semantic embeddings with exact BM25 sparse token scoring in local Qdrant storage.
* **Deterministic Self-Correction:** An active LangGraph evaluation node grades retrieved passages using structured Pydantic schemas. If context is missing or irrelevant, the query is autonomously rewritten into official technical terminology and re-retrieved.
* **Strict Source Attribution:** Diagnostic steps are strictly constrained to cited manual sections, guaranteeing auditable, safety-compliant maintenance guidance.

---

## Architectural Workflow

The system is implemented as a cyclic state machine in **LangGraph**:

```text
Technician Query (e.g., "FlexPendant black screen" or "arm drops slightly on enable")
│
▼
[ NODE: retrieve ] ──> Hybrid Qdrant Search (Dense BGE + Sparse BM25)
│
▼
[ NODE: grade_documents ] ──> Pydantic Binary Evaluator (yes/no per chunk)
│
├── Decision: Are chunks sufficient?
│    │
│    ├── INCORRECT (0 docs) & loop_count < 1
│    │    ▼
│    │   [ NODE: rewrite_query ] (Reformulate slang into ABB terminology)
│    │    │
│    │    └──► Loops back to [ NODE: retrieve ]
│    │
│    └── CORRECT / AMBIGUOUS (or max retries reached)
│         ▼
│        [ NODE: generate ]
│         │
│         └──► Grounded Diagnostic Output with Exact Manual Citations
▼
[ END ]

```
## Theoretical Foundation & Research Background

This system adapts the architecture proposed in the foundational paper:

> **Corrective Retrieval Augmented Generation (CRAG)**  
> *Shi-Qi Yan, Zhi-Jing Hou, Ze-Feng Gao, Xiao-Yin Chen, Chao Shen, Dong-Dong Bai, Fu-Ji Shen, Rong-Kun Fan, Ke-Li Xiao (2024)*  
> [arXiv:2401.15884 [cs.CL]](https://arxiv.org/abs/2401.15884)

### How This Project Translates Theory to Production

The original CRAG paper demonstrates that naive RAG fails when retrievers pull ambiguous or irrelevant chunks, introducing noise into generation. While the reference paper relies on public web search engines (e.g., Google/Tavily) as an external fallback corpus, **this implementation adapts CRAG for closed-domain, safety-critical industrial robotics**:

1. **Closed-Domain Constraint:** Public web search risks pulling conflicting pinouts, voltages, or specifications from other robot vendors (e.g., KUKA, FANUC). All corrective loops are instead constrained to the official ABB IRC5 manual.
2. **Deterministic Grading:** Chunks are filtered through a strict Pydantic evaluator categorizing retrieval quality into `CORRECT`, `AMBIGUOUS`, or `INCORRECT`.
3. **Domain Vocabulary Reformulation:** When technician queries use colloquial shop-floor descriptions (e.g., *"controller pad dead"*), the rewriter translates the query into official ABB catalog terminology (*"FlexPendant power failure DSQC"*) and re-queries the hybrid dense/sparse vector index.

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
│   ├── manuals/                  # Source PDFs (ABB IRC5 3HAC020738-001)
│   └── qdrant_data/              # Persistent local Qdrant vector database
├── docs/                         # Architecture diagrams & specifications
├── src/
│   ├── agent/
│   │   ├── nodes/
│   │   │   ├── retrieve.py       # Qdrant hybrid retrieval node
│   │   │   ├── grader.py         # Pydantic document relevance evaluator
│   │   │   ├── rewriter.py       # Domain-specific query reformulator
│   │   │   └── generate.py       # Citation-grounded synthesis node
│   │   └── state.py              # GraphState schema definition
│   ├── ingestion/                # Chunking and PDF parsing pipeline
│   ├── retrieval/                # Dense + Sparse hybrid Qdrant search
│   └── workflow.py               # Compiled LangGraph CRAG state machine
├── tests/
│   ├── test_crag_nodes.py        # Isolated node unit tests
│   └── test_end_to_end.py        # Multi-turn cyclic graph integration tests
├── requirements.txt
└── README.md

```

---

## Development Setup

### 1. Prerequisites

* Python 3.10+
* Groq API Key

### 2. Installation

```bash
# Clone the repository
git clone <YOUR_GITHUB_REPOSITORY_URL>
cd corrective-agentic-rag-industrial

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 3. Environment Configuration

Set your Groq API key via either method:

**Option A: Windows System Environment Variables (Recommended for Windows)**
1. Press `Win + R`, type `sysdm.cpl`, and press **Enter**.
2. Go to the **Advanced** tab and click **Environment Variables**.
3. Under **User variables**, click **New** and add:
   * **Variable name:** `GROQ_API_KEY`
   * **Variable value:** `your_actual_groq_api_key`
4. Restart your terminal / VS Code so the new variables load.

**Option B: Local `.env` File (Cross-Platform)**
Create a `.env` file in the project root:
```env
GROQ_API_KEY=your_actual_groq_api_key
```

### 4. Running Verification Tests

Run the complete cyclic state graph test suite to verify retrieval, grading, query reformulation, and grounded synthesis:

```bash
python -m tests.test_end_to_end

```