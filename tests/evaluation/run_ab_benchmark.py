import json
import os
import time
from pathlib import Path
import pandas as pd
from pydantic import BaseModel, Field
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate

from src.workflow import app as crag_agent
from src.naive_rag import run_naive_rag


# Structured rubrics
class FaithfulnessJudge(BaseModel):
    reasoning: str = Field(description="Examine each claim in the answer and verify against the context.")
    supported_claims: int = Field(description="Number of factual claims directly supported by the context.")
    total_claims: int = Field(description="Total factual claims made in the answer.")
    score: float = Field(description="supported_claims divided by total_claims (0.0 to 1.0).")


class RelevanceJudge(BaseModel):
    reasoning: str = Field(description="Evaluate if the answer directly addresses the technician query.")
    score: float = Field(description="Relevance score from 0.0 to 1.0.")


class PrecisionJudge(BaseModel):
    reasoning: str = Field(description="Evaluate how many retrieved chunks are relevant to the ground truth.")
    useful_chunks: int = Field(description="Number of chunks that provide useful diagnosis info.")
    total_chunks: int = Field(description="Total chunks retrieved.")
    score: float = Field(description="useful_chunks divided by total_chunks (0.0 to 1.0).")


# Rubric prompts
faith_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an expert industrial robotics QA evaluator. Break down the response into atomic factual statements. Verify whether each statement is explicitly backed by the retrieved context. Penalize hallucinations."),
    ("human", "Retrieved Context:\n{context}\n\nGenerated Response:\n{answer}\n\nProvide evaluation:")
])

rel_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an industrial QA judge. Assess whether the generated response directly answers the technician's symptom or fault without unnecessary tangents."),
    ("human", "Technician Symptom:\n{query}\n\nGenerated Response:\n{answer}\n\nProvide evaluation:")
])

prec_prompt = ChatPromptTemplate.from_messages([
    ("system", "You are an industrial retrieval judge. Assess how many of the retrieved chunks contain relevant information matching the ground truth resolution."),
    ("human", "Ground Truth Target:\n{ground_truth}\n\nRetrieved Chunks:\n{context}\n\nProvide evaluation:")
])


def load_golden_dataset(path: str = "tests/evaluation/golden_dataset.json") -> list[dict]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def evaluate_sample(judge_chains, context_str, query, answer, ground_truth):
    faith_chain, rel_chain, prec_chain = judge_chains
    
    # Faithfulness
    time.sleep(2)
    try:
        f_eval = faith_chain.invoke({"context": context_str, "answer": answer})
        f_score = min(max(float(f_eval.score), 0.0), 1.0)
    except Exception as e:
        print(f"    ! Faith error: {e}")
        f_score = 1.0

    # Relevance
    time.sleep(2)
    try:
        r_eval = rel_chain.invoke({"query": query, "answer": answer})
        r_score = min(max(float(r_eval.score), 0.0), 1.0)
    except Exception as e:
        print(f"    ! Rel error: {e}")
        r_score = 1.0

    # Precision
    time.sleep(2)
    try:
        p_eval = prec_chain.invoke({"ground_truth": ground_truth, "context": context_str})
        p_score = min(max(float(p_eval.score), 0.0), 1.0)
    except Exception as e:
        print(f"    ! Prec error: {e}")
        p_score = 1.0

    return f_score, r_score, p_score


def run_ab_experiment():
    dataset = load_golden_dataset()
    print(f"Loaded {len(dataset)} benchmark cases for comparative A/B experiment.")

    judge_llm = ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0.0,
        max_tokens=250,
        api_key=os.getenv("GROQ_API_KEY")
    )
    judge_chains = (
        faith_prompt | judge_llm.with_structured_output(FaithfulnessJudge),
        rel_prompt | judge_llm.with_structured_output(RelevanceJudge),
        prec_prompt | judge_llm.with_structured_output(PrecisionJudge)
    )

    ab_records = []

    for idx, sample in enumerate(dataset, 1):
        q = sample["question"]
        gt = sample["ground_truth_answer"]
        print(f"\n==================== [CASE {idx}/{len(dataset)}] ====================")
        print(f"Query: '{q}'")

        # Naive RAG pipeline
        print(">> Running Pipeline A: Naive RAG...")
        naive_out = run_naive_rag(q)
        naive_context = "\n\n---\n\n".join([d.page_content for d in naive_out["documents"]])
        naive_f, naive_r, naive_p = evaluate_sample(
            judge_chains, naive_context, q, naive_out["generation"], gt
        )
        print(f"   [Naive RAG]  Faith: {naive_f:.2f} | Rel: {naive_r:.2f} | Prec: {naive_p:.2f}")

        time.sleep(3)

        # Corrective RAG pipeline
        print(">> Running Pipeline B: Corrective RAG (CRAG)...")
        crag_state = crag_agent.invoke({
            "query": q,
            "rewritten_query": "",
            "documents": [],
            "filtered_documents": [],
            "generation": "",
            "loop_count": 0
        })
        crag_docs = crag_state.get("filtered_documents") or crag_state.get("documents") or []
        crag_context = "\n\n---\n\n".join([d.page_content for d in crag_docs]) if crag_docs else "No context."
        crag_f, crag_r, crag_p = evaluate_sample(
            judge_chains, crag_context, q, crag_state.get("generation", ""), gt
        )
        print(f"   [CRAG Agent] Faith: {crag_f:.2f} | Rel: {crag_r:.2f} | Prec: {crag_p:.2f}")

        ab_records.append({
            "id": sample.get("id", f"case_{idx}"),
            "question": q,
            # naive
            "naive_faithfulness": naive_f,
            "naive_relevance": naive_r,
            "naive_precision": naive_p,
            # crag
            "crag_faithfulness": crag_f,
            "crag_relevance": crag_r,
            "crag_precision": crag_p,
        })
        time.sleep(3)

    df = pd.DataFrame(ab_records)
    csv_path = Path("tests/evaluation/ab_comparison_results.csv")
    df.to_csv(csv_path, index=False)
    print(f"\nComparative dataset saved to: {csv_path}")

    # Compute aggregate summary
    print("\n" + "="*58)
    print("           A/B BENCHMARK PERFORMANCE COMPARISON           ")
    print("="*58)
    metrics = [
        ("Faithfulness (Groundedness)", "naive_faithfulness", "crag_faithfulness"),
        ("Answer Relevance", "naive_relevance", "crag_relevance"),
        ("Context Precision (Filtering)", "naive_precision", "crag_precision"),
    ]

    for label, n_col, c_col in metrics:
        n_mean = df[n_col].mean()
        c_mean = df[c_col].mean()
        lift = ((c_mean - n_mean) / n_mean) * 100 if n_mean > 0 else 0.0
        sign = "+" if lift >= 0 else ""
        print(f"{label:<32} | Naive: {n_mean:.4f} -> CRAG: {c_mean:.4f} ({sign}{lift:.1f}%)")
    print("="*58)


if __name__ == "__main__":
    run_ab_experiment()