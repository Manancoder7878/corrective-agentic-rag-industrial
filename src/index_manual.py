from src.ingestion.pdf_parser import load_pdf_pages
from src.ingestion.chunking import split_manual_documents
from src.retrieval.vector_store import build_or_load_vector_store

def main():
    pdf_path = "data/manuals/abb_irc5_troubleshooting.pdf"

    print(f"Loading pages from: {pdf_path}...")
    pages = load_pdf_pages(pdf_path)
    
    print("Splitting into documents...")
    chunks = split_manual_documents(pages)
    print(f"Total chunks prepared: {len(chunks)}")

    print("Indexing into local Qdrant collection...")
    vector_store = build_or_load_vector_store(chunks=chunks)
    print("Indexing complete! Data persisted to data/qdrant_data.")

    # Verification query using MMR
    test_query = "FlexPendant screen stays black during boot"
    print(f"\n--- Testing MMR Search: '{test_query}' ---")
    results = vector_store.max_marginal_relevance_search(
        query=test_query, 
        k=3, 
        fetch_k=8, 
        lambda_mult=0.7
    )

    for i, doc in enumerate(results, 1):
        raw_page = doc.metadata.get("page", 0)
        pdf_sheet = raw_page + 1       # matches adobe acrobats page counter box
        printed_page = pdf_sheet - 2   # matches page footer printed on the manual

        print(f"\nResult {i}:")
        print(f"Source: {doc.metadata.get('source')} | PDF Sheet: {pdf_sheet} (Manual Page: {printed_page})")
        print(f"Chunk ID: {doc.metadata.get('chunk_id')}")
        print(f"Snippet: {doc.page_content[:200]}...")

if __name__ == "__main__":
    main()