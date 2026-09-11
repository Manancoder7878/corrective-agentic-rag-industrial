from src.ingestion.pdf_parser import load_pdf_pages
from src.ingestion.chunking import split_manual_documents


def main():
    manual_path = "data/manuals/abb_irc5_troubleshooting.pdf"

    print(f"Loading pages from: {manual_path}...")
    raw_docs = load_pdf_pages(manual_path)
    print(f"Loaded {len(raw_docs)} pages.")

    print("Splitting into chunks and cleaning metadata...")
    chunks = split_manual_documents(raw_docs)
    print(f"Total chunks created: {len(chunks)}")

    print("\n--- Sample Chunk Verification ---")
    print(f"Metadata: {chunks[0].metadata}")
    print(f"Content Preview: {chunks[0].page_content[:500]}...")


if __name__ == "__main__":
    main()