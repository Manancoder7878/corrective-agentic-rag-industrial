from src.agent.state import GraphState
from src.agent.nodes.retrieve import retrieve_node
from src.agent.nodes.grader import grade_documents_node, decide_to_generate


def run_pipeline_step(query: str):
    print(f"\n================ TESTING QUERY: '{query}' ================")
    state: GraphState = {
        "query": query,
        "rewritten_query": "",
        "documents": [],
        "filtered_documents": [],
        "generation": "",
        "loop_count": 0
    }

    state.update(retrieve_node(state))

    state.update(grade_documents_node(state))

    print(f"Total Docs Retrieved: {len(state['documents'])}")
    print(f"Total Relevant Docs Kept: {len(state['filtered_documents'])}")

    decision = decide_to_generate(state)
    print(f"Decision routing: -> {decision}")
    return state, decision


def test_positive_case():
    state, decision = run_pipeline_step("FlexPendant screen stays black during boot")
    assert len(state["filtered_documents"]) > 0
    assert decision == "generate"


def test_negative_case():
    state, decision = run_pipeline_step("How do I make chocolate cake with strawberries?")
    assert len(state["filtered_documents"]) == 0
    assert decision == "rewrite_query"


if __name__ == "__main__":
    test_positive_case()
    test_negative_case()
    print("\n All node tests passed successfully!")