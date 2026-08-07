from answer_engine.intent import parse_intent, retrieval_query


def test_parse_intent():
    assert parse_intent("What is grounding?") == "factual"
    assert parse_intent("What is the difference between a workflow and an agent?") == "comparison"
    assert parse_intent("How should I embed citations?") == "how_to"


def test_retrieval_query_biases_comparison():
    q = retrieval_query("workflow vs agent", "comparison")
    assert "difference" in q or "compare" in q
