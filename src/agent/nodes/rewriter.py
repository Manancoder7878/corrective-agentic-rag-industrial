from typing import Any, Dict
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_groq import ChatGroq
from src.agent.state import GraphState

def rewrite_query_node(state: GraphState) -> Dict[str, Any]:
    """
    Transforms the users query into an optimized technical search query
    tailored to ABB IRC5 technical manual terminology
    """
    print("--- [NODE: REWRITE QUERY] Reformulating search query ---")
    query = state["query"]
    loop_count = state.get("loop_count", 0)

    llm = ChatGroq(
    model="openai/gpt-oss-20b",
    temperature=0
    )

    system_prompt = (
        "You are a senior robotics service engineer. A technician entered a diagnostic query "
        "that failed to retrieve matching documentation in the ABB IRC5 manual.\n"
        "Rephrase or expand the query using official technical terms, subsystem names (e.g., FlexPendant, "
        "SMB, Main Computer, Axis Computer, Drive Module, Safety Chain), or symptom categories.\n"
        "Return ONLY the reformulated query string, nothing else."
    )

    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original query: {query}\n\nReformulated technical query:")
    ])

    rewriter_chain = rewrite_prompt | llm | StrOutputParser()
    new_query = rewriter_chain.invoke({"query": query}).strip()

    print(f"  -> Reformulated to: '{new_query}'")
    return {
        "rewritten_query": new_query,
        "loop_count": loop_count + 1
    }