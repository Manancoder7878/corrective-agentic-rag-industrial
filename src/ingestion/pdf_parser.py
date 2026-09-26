from pathlib import Path

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document


def load_pdf_pages(file_path: str | Path) -> list[Document]:
    #Loading pdf pages as langChain document objects
    pdf_path = Path(file_path)
    if not pdf_path.exists():
        raise FileNotFoundError(f"Manual not found at: {pdf_path}")

    loader = PyPDFLoader(str(pdf_path))
    return loader.load()