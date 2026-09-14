"""
Baseline Naive RAG Pipeline (No Grading, No Query Rewriting, No Self-Correction).
Used as Pipeline A in comparative A/B evaluation benchmarking.
"""
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
import os

from src.retrieval.hybrid import get_hybrid_retriever

# 1. Direct prompt without self-corrective safety mechanisms
naive_rag_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "You are an industrial robotics maintenance technician assistant. "
        "Use the provided context to answer the user's troubleshooting question. "
        "If you do not know the answer, use your technical knowledge to assist."
    ),
    (
        "human",
        "Retrieved Context:\n{context}\n\nTroubleshooting Question: {question}\n\nProvide diagnostic steps:"
    )
])


def run_naive_rag(question: str) -> dict:
    """
    Executes standard Naive RAG:
    Query -> Retrieve Top 4 Chunks -> Direct LLM Generation
    """
    retriever = get_hybrid_retriever(top_k=4)
    
    # 1. Retrieve raw chunks (no grading, no filtering)
    raw_docs = retriever.retrieve(question,top_k=4)
    
    # 2. Synthesize directly
    context_text = "\n\n---\n\n".join([doc.page_content for doc in raw_docs])
    
    llm = ChatGroq(
        model="qwen/qwen3.8-27b",
        temperature=0.0,
        api_key=os.getenv("GROQ_API_KEY"),
        max_tokens=600,
    )
    
    chain = naive_rag_prompt | llm
    response = chain.invoke({"context": context_text, "question": question})
    
    return {
        "question": question,
        "documents": raw_docs,
        "generation": response.content
    }