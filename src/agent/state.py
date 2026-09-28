from typing import TypedDict

from langchain_core.documents import Document


class GraphState(TypedDict):
    """
    Represents the state of industrial CRAG graph

    Attributes:
        query: User's original diagnostic question or fault code
        rewritten_query: Refined query if initial retrieval lacked relevance
        documents: List of candidate chunks retrieved from qdrant
        filtered_documents: List of chunks validated by the grader
        generation: Final synthesized troubleshooting answer with citations
        loop_count: Guard counter to prevent infinite query-rewrite loops
    """
    query: str
    rewritten_query: str
    documents: list[Document]
    filtered_documents: list[Document]
    generation: str
    loop_count: int