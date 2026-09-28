
from langchain_core.documents import Document

from src.retrieval.vector_store import build_or_load_hybrid_store


class IndustrialHybridRetriever:
    # Production retriever combining dense semantic and sparse BM25 retrieval over the documentation
    def __init__(self, top_k: int = 3):
        self.top_k = top_k
        self.vector_store = build_or_load_hybrid_store()

    def retrieve(self, query: str, top_k: int | None = None) -> list[Document]:
        # Runs native qdrant hybrid retrieval with reciprocal rank fusion
        k = top_k or self.top_k
        return self.vector_store.similarity_search(query=query, k=k)


def get_hybrid_retriever(top_k: int = 3) -> IndustrialHybridRetriever:
    return IndustrialHybridRetriever(top_k=top_k)