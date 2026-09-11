from typing import List
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter


def split_manual_documents(
    documents: List[Document], 
    chunk_size: int = 600, 
    chunk_overlap: int = 60
) -> List[Document]:
    # Splits loaded langchain documents and prunes bloat metadata
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
        separators=["\n\n", "\n", ". ", " ", ""]
    )

    chunks = splitter.split_documents(documents)

    for idx, chunk in enumerate(chunks):
        doc_source = chunk.metadata.get("source", "abb_irc5_troubleshooting.pdf").split("/")[-1]
        page_num = chunk.metadata.get("page_label", chunk.metadata.get("page", 0))

        # Overwrite with only lean, deterministic metadata needed for retrieval and citations
        chunk.metadata = {
            "source": doc_source,
            "doc_id": "3HAC020738-001",
            "page": int(page_num) if str(page_num).isdigit() else chunk.metadata.get("page", 0),
            "chunk_id": f"irc5_p{page_num}_c{idx + 1}"
        }

    return chunks