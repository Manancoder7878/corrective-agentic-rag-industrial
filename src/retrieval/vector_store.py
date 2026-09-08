from pathlib import Path
from typing import List
from langchain_core.documents import Document
from langchain_qdrant import Qdrant
from langchain_community.embeddings.fastembed import FastEmbedEmbeddings

COLLECTION_NAME = "abb_irc5_troubleshooting"
DEFAULT_DB_PATH = Path("data/qdrant_data")

def get_embedding_model() -> FastEmbedEmbeddings:
    # returns local, lightweight fastembed embeddings model
    return FastEmbedEmbeddings(model_name="BAAI/bge-small-en-v1.5")

def build_or_load_vector_store(
    chunks: List[Document] = None,
    persist_path: Path = DEFAULT_DB_PATH,
    collection_name: str = COLLECTION_NAME
) -> Qdrant:
    """
    Builds a persistent local Qdrant collection if chunks are provided,
    or connects to the existing local index on disk.
    """
    embeddings = get_embedding_model()
    persist_path.mkdir(parents=True, exist_ok=True)

    if chunks:
        # Build and store new embeddings locally
        vector_store = Qdrant.from_documents(
            documents=chunks,
            embedding=embeddings,
            path=str(persist_path),
            collection_name=collection_name
        )
        return vector_store

    # Load existing local collection without re-indexing
    return Qdrant.from_existing_collection(
        embedding=embeddings,
        path=str(persist_path),
        collection_name=collection_name
    )