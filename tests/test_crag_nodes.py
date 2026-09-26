from unittest.mock import patch

from langchain_core.documents import Document

from src.agent.nodes.grader import (
    GradeDocuments,
    decide_to_generate,
    grade_documents_node,
)

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


@patch("langchain_core.runnables.base.RunnableSequence.invoke")
def test_positive_case(mock_invoke):
    mock_invoke.return_value = GradeDocuments(binary_score="yes")

    state = {
        "query": "FlexPendant screen stays black during boot",
        "documents": ROBOTICS_DOCS,
        "loop_count": 0,
    }

    graded_state = grade_documents_node(state)
    decision = decide_to_generate(graded_state)

    assert len(graded_state["filtered_documents"]) == 1
    assert decision == "generate"


@patch("langchain_core.runnables.base.RunnableSequence.invoke")
def test_negative_case(mock_invoke):
    mock_invoke.return_value = GradeDocuments(binary_score="no")

    state = {
        "query": "How do I make chocolate cake with strawberries?",
        "documents": CAKE_DOCS,
        "loop_count": 0,
    }

    graded_state = grade_documents_node(state)
    decision = decide_to_generate(graded_state)

    assert len(graded_state["filtered_documents"]) == 0
    assert decision == "rewrite_query"