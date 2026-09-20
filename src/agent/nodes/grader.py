from typing import Any, Dict, List
from pydantic import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_groq import ChatGroq
from langchain_core.documents import Document
from src.agent.state import GraphState

class GradeDocuments(BaseModel):
    """Binary scoring model for document relevance assessment"""
    binary_score: str = Field(
        description="Relevance score: 'yes' if document is relevant to query, 'no' otherwise.",
        pattern="^(yes|no)$"
    )

def grade_documents_node(state: GraphState) -> Dict[str, Any]:
    """
    Evaluates retrieved chunks for relevance to the diagnostic query
    filters out noise and irrelevant sections
    """
    print("--- [NODE: GRADE DOCUMENTS] Evaluating retrieved chunks ---")
    query = state["query"]
    documents = state["documents"]

    llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0
    )
    structured_llm_grader = llm.with_structured_output(GradeDocuments)

    system_prompt = (
        "You are an industrial diagnostics evaluator for ABB IRC5 robot manuals.\n"
        "Your job is to assess if a retrieved manual snippet is relevant to troubleshooting the user's issue.\n"
        "If the document mentions relevant error codes, symptoms, electrical checks, or safety instructions: grade 'yes'.\n"
        "If it is completely unrelated or generic table of contents filler: grade 'no'."
    )

    grade_prompt = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        ("human", "Retrieved document:\n\n{document}\n\nUser diagnostic query: {query}")
    ])

    evaluator_chain = grade_prompt | structured_llm_grader

    filtered_docs: List[Document] = []
    for doc in documents:
        result = evaluator_chain.invoke({"query": query, "document": doc.page_content})
        grade = result.binary_score.lower()

        if grade == "yes":
            print(f"  -> Keep: [Page {doc.metadata.get('page')}] {doc.metadata.get('chunk_id')}")
            filtered_docs.append(doc)
        else:
            print(f"  -> Drop: [Page {doc.metadata.get('page')}] (Not relevant)")

    return {"documents": documents,"filtered_documents": filtered_docs}

def decide_to_generate(state: GraphState) -> str:
    """
    Evaluates whether to proceed to generation or trigger corrective query rewriting
    Explicitly tracks correct, ambiguous, and incorrect states
    """
    documents = state.get("documents", [])
    filtered_documents = state.get("filtered_documents", [])
    loop_count = state.get("loop_count", 0)

    # Infinite loop guard
    if loop_count >= 1:
        print("--- [DECISION] Max rewrite retries reached. Forcing generation fallback. ---")
        return "generate"

    # Incorrect - Confidence below lower threshold
    if not filtered_documents:
        print("--- [CRAG EVALUATION: INCORRECT] All chunks irrelevant. Triggering query rewrite. ---")
        return "rewrite_query"

    # Ambiguous - Partial match / some noise filtered
    if len(filtered_documents) < len(documents):
        print(f"--- [CRAG EVALUATION: AMBIGUOUS] Kept {len(filtered_documents)}/{len(documents)} relevant chunks. Proceeding to generation. ---")
        return "generate"

    # Correct - High confidence across all retrieved chunks
    print(f"--- [CRAG EVALUATION: CORRECT] All {len(documents)} chunks relevant. Proceeding to generation. ---")
    return "generate"