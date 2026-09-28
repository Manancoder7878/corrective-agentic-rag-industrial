from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq

from src.agent.state import GraphState


def format_docs_with_sources(docs: list[Document]) -> str:
    # Formats retrieved chunks with exact page numbers and chunk ids
    formatted = []
    for doc in docs:
        page = doc.metadata.get("page", "Unknown")
        chunk_id = doc.metadata.get("chunk_id", "Unknown")
        snippet = doc.page_content.strip()
        formatted.append(f"--- [SOURCE: Manual Page {page} | Chunk ID: {chunk_id}] ---\n{snippet}\n")
    return "\n".join(formatted)


def generate_node(state: GraphState) -> dict[str, Any]:
    """
    Synthesizes a diagnostic answer strictly grounded on
    the filtered ABB IRC5 documentation chunks
    """
    print("--- [NODE: GENERATE] Synthesizing diagnostic response ---")
    query = state["query"]
    filtered_docs = state.get("filtered_documents", [])

    # If no valid docs exist even after the corrective loop
    if not filtered_docs:
        fallback_msg = (
            "No authoritative troubleshooting procedures for this specific issue "
            "could be validated in the ABB IRC5 manual (3HAC020738-001). "
            "Please verify the exact event code or consult ABB Product Support directly."
        )
        return {"generation": fallback_msg}

    context_str = format_docs_with_sources(filtered_docs)

    llm = ChatGroq(
        model="openai/gpt-oss-120b",
        temperature=0
    )

    system_prompt = (
        "You are an expert ABB Robotics service engineer specialized in IRC5 controller troubleshooting.\n"
        "Your task is to provide clear, actionable diagnostic instructions strictly based on the provided manual excerpts.\n\n"
        "STRICT CONSTRAINTS:\n"
        "1. ONLY state facts, causes, and steps directly supported by the provided text.\n"
        "2. DO NOT hallucinate wiring pinouts, voltages, or part numbers not explicitly mentioned.\n"
        "3. Explicitly cite the manual page numbers in your text (e.g., [Page 40]).\n"
        "4. Format your output into four distinct sections:\n"
        "   - **Problem / Description**\n"
        "   - **Probable Causes**\n"
        "   - **Recommended Actions** (ordered step-by-step)\n"
        "   - **Manual Citations** (list pages and chunk IDs used)"
    )

    prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        (
            "human",
            (
                "Context from ABB IRC5 Troubleshooting Manual:\n{context}\n\n"
                "Technician Diagnostic Query: {query}\n\n"
                "Provide grounded troubleshooting steps with citations:"
            )
        )
    ])

    rag_chain = prompt | llm | StrOutputParser()
    generation = rag_chain.invoke({"context": context_str, "query": query})

    return {"generation": generation}

