from typing import Any

from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.agent.state import GraphState


def rewrite_query_node(state: GraphState) -> dict[str, Any]:
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
        "You are a senior robotics service engineer specialized in ABB IRC5 controllers.\n"
        "A technician entered a diagnostic query that returned zero relevant manual excerpts.\n"
        "Your job is to rewrite or expand the query using official ABB technical terminology "
        "(e.g., FlexPendant, SMB, Main Computer, Axis Computer, Drive Module, Safety Chain, DC Link).\n\n"
        "CRITICAL RULE: If the query is completely unrelated to robotics, industrial equipment, "
        "or electrical/mechanical troubleshooting (e.g., cooking, pop culture, trivia), "
        "DO NOT force ABB terms into it. Simply return the original query unchanged.\n"
        "Return ONLY the reformulated query string, nothing else."
    )

    rewrite_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Original query: {query}\n\nReformulated technical query:")
    ])

    rewriter_chain = rewrite_prompt | llm | StrOutputParser()
    new_query = rewriter_chain.invoke({"query": query}).strip()

    # Fall back to original query if rewriter returns empty text
    if not new_query:
        new_query = query
    
    print(f"  -> Reformulated to: '{new_query}'")
    return {
        "rewritten_query": new_query,
        "loop_count": loop_count + 1
    }