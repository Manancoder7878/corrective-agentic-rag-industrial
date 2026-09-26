from typing import Any

from src.agent.state import GraphState
from src.retrieval.hybrid import get_hybrid_retriever


def retrieve_node(state: GraphState) -> dict[str, Any]:
    """
    Retrieves candidate documents from persistent qdrant index
    using hybrid dense and sparse search
    """
    search_query = state.get("rewritten_query") or state["query"]
    print(f"--- [NODE: RETRIEVE] Searching for: '{search_query}' ---")

    retriever = get_hybrid_retriever(top_k=4)
    documents = retriever.retrieve(search_query)

    return {"documents": documents}
