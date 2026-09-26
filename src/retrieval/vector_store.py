import os
from pathlib import Path

from langchain_community.embeddings.fastembed import FastEmbedEmbeddings
from langchain_core.documents import Document
from langchain_qdrant import FastEmbedSparse, QdrantVectorStore, RetrievalMode

COLLECTION_NAME = "abb_irc5_hybrid"
DEFAULT_DB_PATH = Path("data/qdrant_data")

CACHE_DIR = os.getenv("FASTEMBED_CACHE_PATH", "/app/.cache/fastembed")

def get_dense_embeddings() -> FastEmbedEmbeddings:
    # Dense embedding model for semantic intent
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5", cache_dir=CACHE_DIR)

def get_sparse_embeddings() -> FastEmbedSparse:
    # Sparse BM25 model for alphanumeric event codes and part identifiers
    return FastEmbedSparse(model_name="Qdrant/bm25", cache_dir=CACHE_DIR)

def build_or_load_hybrid_store(
    chunks: list[Document] | None = None,
    persist_path: Path = DEFAULT_DB_PATH,
    collection_name: str = COLLECTION_NAME
) -> QdrantVectorStore:
    # Builds or loads a persistent qdrant collection supporting native hybrid search
    dense_embeddings = get_dense_embeddings()
    sparse_embeddings = get_sparse_embeddings()
    persist_path.mkdir(parents=True, exist_ok=True)

    if chunks:
        # Build new hybrid index(both dense and sparse vectors computed)
        vector_store = QdrantVectorStore.from_documents(
            documents=chunks,
            embedding=dense_embeddings,
            sparse_embedding=sparse_embeddings,
            retrieval_mode=RetrievalMode.HYBRID,
            path=str(persist_path),
            collection_name=collection_name
        )
        return vector_store

    # Load existing local collection(hybrid) without re-indexing
    return QdrantVectorStore.from_existing_collection(
        embedding=dense_embeddings,
        sparse_embedding=sparse_embeddings,
        retrieval_mode=RetrievalMode.HYBRID,
        path=str(persist_path),
        collection_name=collection_name
    )