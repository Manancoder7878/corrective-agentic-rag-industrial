from langchain_core.documents import Document
from src.agent.nodes.grader import grade_documents_node

# Sample documents for testing
ROBOTICS_DOCS = [
    Document(
        page_content="FlexPendant black screen: Check power supply cable and contactor K42 on IRC5 controller.",
        metadata={"page": 102},
    )
]

CAKE_DOCS = [
    Document(
        page_content="Ingredients: 200g flour, 100g sugar, cocoa powder, fresh strawberries.",
        metadata={"page": 1},
    )
]


def test_positive_case():
    # Verify that relevant documents are accepted into filtered_documents
    state = {
        "query": "FlexPendant screen stays black during boot",
        "documents": ROBOTICS_DOCS,
        "retry_count": 0,
    }

    graded_state = grade_documents_node(state)

    filtered = graded_state.get("filtered_documents", [])
    assert len(filtered) > 0
    assert "FlexPendant" in filtered[0].page_content


def test_negative_case():
    # Verify that irrelevant documents are dropped from filtered_documents
    state = {
        "query": "How do I make chocolate cake with strawberries?",
        "documents": CAKE_DOCS,
        "retry_count": 0,
    }

    graded_state = grade_documents_node(state)

    filtered = graded_state.get("filtered_documents", [])
    assert len(filtered) == 0