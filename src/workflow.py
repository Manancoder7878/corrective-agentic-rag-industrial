from langgraph.graph import StateGraph, END
from src.agent.state import GraphState
from src.agent.nodes.retrieve import retrieve_node
from src.agent.nodes.grader import grade_documents_node, decide_to_generate
from src.agent.nodes.rewriter import rewrite_query_node
from src.agent.nodes.generate import generate_node

def build_crag_workflow():
    workflow = StateGraph(GraphState)

    # Nodes
    workflow.add_node("retrieve", retrieve_node)
    workflow.add_node("grade_documents", grade_documents_node)
    workflow.add_node("rewrite_query", rewrite_query_node)
    workflow.add_node("generate", generate_node)

    # Fixed edges
    workflow.set_entry_point("retrieve")
    workflow.add_edge("retrieve", "grade_documents")
    workflow.add_edge("rewrite_query", "retrieve")
    workflow.add_edge("generate", END)

    # Conditional Edge
    workflow.add_conditional_edges(
        "grade_documents",
        decide_to_generate,
        {
            "generate": "generate",
            "rewrite_query": "rewrite_query",
        }
    )

    return workflow.compile()


app = build_crag_workflow()