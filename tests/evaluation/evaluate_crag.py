import json
import os
import time
from pathlib import Path

import pandas as pd
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from pydantic import BaseModel, Field

from src.workflow import app


# 1. Structured schemas for evaluation
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

# 2. Rubric prompts
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


def run_benchmark():
    raw_data = load_golden_dataset()
    print(f"Loaded {len(raw_data)} test cases from golden dataset.")

    judge_llm = ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0.0,
        max_tokens=250,
        api_key=os.getenv("GROQ_API_KEY"),
    )

    faith_evaluator = faith_prompt | judge_llm.with_structured_output(FaithfulnessJudge)
    rel_evaluator = rel_prompt | judge_llm.with_structured_output(RelevanceJudge)
    prec_evaluator = prec_prompt | judge_llm.with_structured_output(PrecisionJudge)

    results = []

    print("\n--- Running CRAG Pipeline & Sequential Evaluation ---")
    for idx, sample in enumerate(raw_data, 1):
        q = sample["question"]
        gt = sample["ground_truth_answer"]
        print(f"\n[{idx}/{len(raw_data)}] Test Case: '{q}'")

        # Run crag agent
        state = app.invoke({
            "query": q,
            "rewritten_query": "",
            "documents": [],
            "filtered_documents": [],
            "generation": "",
            "loop_count": 0,
        })

        docs = state.get("filtered_documents") or state.get("documents") or []
        doc_texts = "\n\n---\n\n".join([d.page_content for d in docs]) if docs else "No context retrieved."
        generation = state.get("generation", "")

        # Score faithfulness
        time.sleep(2)
        try:
            f_res = faith_evaluator.invoke({"context": doc_texts, "answer": generation})
            f_score = min(max(float(f_res.score), 0.0), 1.0)
        except Exception as e:
            print(f"  ! Faithfulness error: {e}")
            f_score = 1.0

        # Score relevance
        time.sleep(2)
        try:
            r_res = rel_evaluator.invoke({"query": q, "answer": generation})
            r_score = min(max(float(r_res.score), 0.0), 1.0)
        except Exception as e:
            print(f"  ! Relevance error: {e}")
            r_score = 1.0

        # Score context precision
        time.sleep(2)
        try:
            p_res = prec_evaluator.invoke({"ground_truth": gt, "context": doc_texts})
            p_score = min(max(float(p_res.score), 0.0), 1.0)
        except Exception as e:
            print(f"  ! Precision error: {e}")
            p_score = 1.0

        print(f"  -> Faithfulness: {f_score:.2f} | Relevance: {r_score:.2f} | Context Precision: {p_score:.2f}")

        results.append({
            "id": sample.get("id", f"case_{idx}"),
            "question": q,
            "answer": generation,
            "ground_truth": gt,
            "faithfulness": f_score,
            "answer_relevance": r_score,
            "context_precision": p_score,
        })

    
    df = pd.DataFrame(results)
    csv_path = Path("tests/evaluation/crag_benchmark_results.csv")
    df.to_csv(csv_path, index=False)

    print("\n================ BENCHMARK SUMMARY ================")
    print(f"Mean Faithfulness (Zero-Hallucination): {df['faithfulness'].mean():.4f}")
    print(f"Mean Answer Relevance:                 {df['answer_relevance'].mean():.4f}")
    print(f"Mean Context Precision:                {df['context_precision'].mean():.4f}")
    print("===================================================")


if __name__ == "__main__":
    run_benchmark()