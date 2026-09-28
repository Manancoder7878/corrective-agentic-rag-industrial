from src.workflow import app


def run_pipeline(query: str):
    print(f"\n{'='*70}\nSTARTING RUN FOR QUERY: '{query}'\n{'='*70}")

    initial_state = {
        "query": query,
        "rewritten_query": "",
        "documents": [],
        "filtered_documents": [],
        "generation": "",
        "loop_count": 0,
    }

    final_state = app.invoke(initial_state)

    print("\n" + "=" * 25 + " AGENT DIAGNOSTIC OUTPUT " + "=" * 25)
    print(final_state["generation"])
    print("=" * 73)

    return final_state


def test_handheld_pad_diagnostic():
    query = "robot handheld control pad won't turn on or show anything"
    result = run_pipeline(query)

    assert len(result["filtered_documents"]) > 0, (
        "Rewrite failed to retrieve relevant documents."
    )
    assert "FlexPendant" in result["generation"] or "power" in result["generation"].lower(), (
        "Expected FlexPendant or power resolution in final output."
    )


def test_motor_noise_arm_drop_diagnostic():
    query = "motors making loud squealing or clicking noise and arm drops slightly when enabling"
    result = run_pipeline(query)

    assert len(result["filtered_documents"]) > 0, (
        "Failed to retrieve or recover valid troubleshooting documents after rewrite."
    )
    assert any(term in result["generation"].lower() for term in ["brake", "motor", "drive", "mechanical"]), (
        "Expected brake, motor, or drive troubleshooting steps in the final diagnosis."
    )


if __name__ == "__main__":
    test_handheld_pad_diagnostic()
    test_motor_noise_arm_drop_diagnostic()
    print("\n All tests passed successfully!")