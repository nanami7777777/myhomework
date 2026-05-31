from app.core.graph import build_reasoning_graph
from app.core.models import ContextDoc, HotpotSample, SupportingFact


def test_build_reasoning_graph_links_question_supporting_sentences_and_answer():
    sample = HotpotSample(
        id="sample-graph",
        subset="distractor",
        split="validation",
        question="Which work came first, Arthur's Magazine or First for Women?",
        answer="Arthur's Magazine",
        type="comparison",
        level="medium",
        context_docs=[
            ContextDoc(title="Arthur's Magazine", sentences=["Arthur's Magazine started in 1844."]),
            ContextDoc(title="First for Women", sentences=["First for Women started in 1989."]),
        ],
        supporting_facts=[
            SupportingFact(title="Arthur's Magazine", sent_id=0),
            SupportingFact(title="First for Women", sent_id=0),
        ],
    )

    graph = build_reasoning_graph(sample)

    node_ids = {node["id"] for node in graph["nodes"]}
    edge_types = {edge["kind"] for edge in graph["edges"]}

    assert "question" in node_ids
    assert "answer" in node_ids
    assert "title:Arthur's Magazine" in node_ids
    assert "sentence:Arthur's Magazine:0" in node_ids
    assert edge_types == {"mentions", "supports", "leads_to"}
