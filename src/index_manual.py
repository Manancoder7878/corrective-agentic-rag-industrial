from src.ingestion.pdf_parser import load_pdf_pages
from src.ingestion.chunking import split_manual_documents
from src.retrieval.vector_store import build_or_load_hybrid_store
from src.retrieval.hybrid import get_hybrid_retriever

def main():
    pdf_path = "data/manuals/abb_irc5_troubleshooting.pdf"

    print(f"Loading pages from: {pdf_path}...")
    pages = load_pdf_pages(pdf_path)
    
    print("Splitting into documents...")
    chunks = split_manual_documents(pages)
    print(f"Total chunks prepared: {len(chunks)}")

    print("Building Hybrid Qdrant Index (Dense + BM25)...")
    build_or_load_hybrid_store(chunks=chunks)
    print("Hybrid indexing complete and persisted!")

    retriever = get_hybrid_retriever(top_k=2)

    code_query = "110710"
    print(f"\n================ TEST 1: Exact Event Code '{code_query}' ================")
    code_results = retriever.retrieve(code_query, top_k=2)
    for i, doc in enumerate(code_results, 1):
        print(f"[{i}] Page: {doc.metadata.get('page')} | Chunk: {doc.metadata.get('chunk_id')}")
        print(f"    Snippet: {doc.page_content[:180]}...\n")

    symptom_query = "FlexPendant screen blank when starting"
    print(f"================ TEST 2: Semantic Symptom '{symptom_query}' ================")
    symptom_results = retriever.retrieve(symptom_query, top_k=2)
    for i, doc in enumerate(symptom_results, 1):
        print(f"[{i}] Page: {doc.metadata.get('page')} | Chunk: {doc.metadata.get('chunk_id')}")
        print(f"    Snippet: {doc.page_content[:180]}...\n")

if __name__ == "__main__":
    main()