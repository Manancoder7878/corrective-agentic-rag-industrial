from src.workflow import app

def test_full_pipeline(query: str):
    print(f"\n{'='*70}\nSTARTING RUN FOR QUERY: '{query}'\n{'='*70}")
    
    initial_state = {
        "query": query,
        "rewritten_query": "",
        "documents": [],
        "filtered_documents": [],
        "generation": "",
        "loop_count": 0
    }

    final_state = app.invoke(initial_state)

    print("\n" + "="*25 + " AGENT DIAGNOSTIC OUTPUT " + "="*25)
    print(final_state["generation"])
    print("="*73)
    
    return final_state


if __name__ == "__main__":
    # Diagnostic query
    result_1 = test_full_pipeline("robot handheld control pad won't turn on or show anything")
    assert len(result_1["filtered_documents"]) > 0, "Rewrite failed to retrieve relevant documents."
    assert "FlexPendant" in result_1["generation"] or "power" in result_1["generation"].lower()

    # Vague symptom query, noisy motor + arm dropping on enable
    result_2 = test_full_pipeline("motors making loud squealing or clicking noise and arm drops slightly when enabling")
    
    assert len(result_2["filtered_documents"]) > 0, (
        "Failed to retrieve or recover valid troubleshooting documents after rewrite."
    )
    assert any(term in result_2["generation"].lower() for term in ["brake", "motor", "drive", "mechanical"]), (
        "Expected brake, motor, or drive troubleshooting steps in the final diagnosis."
    )
    
    print("\n All tests passed successfully!")