from answer_engine.retrieval import Passage
from answer_engine.synthesis import assemble_prompt, extract_citations, offline_synthesize


def test_assemble_embeds_citations_before_generation():
    passages = [
        Passage(id="grounding#0", text="Grounding means claims cite evidence.", doc_id="grounding")
    ]
    system, user = assemble_prompt("What is grounding?", passages)
    assert "[grounding#0]" in system
    assert "Evidence passages" in system
    assert user == "What is grounding?"


def test_offline_synthesize_cites():
    passages = [
        Passage(id="latency-budget#0", text="An answer engine has a latency budget.", doc_id="latency-budget")
    ]
    answer = offline_synthesize("why no loop?", passages)
    assert "[latency-budget#0]" in answer
    assert extract_citations(answer) == ["latency-budget#0"]
