from app.core.clustering import cluster_records
from app.core.models import ContextDoc, HotpotSample, SupportingFact


SAMPLE_A = HotpotSample(
    id="a",
    subset="distractor",
    split="validation",
    question="Which city is the capital of France?",
    answer="Paris",
    type="bridge",
    level="easy",
    context_docs=[ContextDoc(title="Paris", sentences=["Paris is the capital city of France."])],
    supporting_facts=[SupportingFact(title="Paris", sent_id=0)],
)

SAMPLE_B = HotpotSample(
    id="b",
    subset="distractor",
    split="validation",
    question="What city serves as the capital of France?",
    answer="Paris",
    type="bridge",
    level="easy",
    context_docs=[ContextDoc(title="Paris", sentences=["Paris is the capital city of France."])],
    supporting_facts=[SupportingFact(title="Paris", sent_id=0)],
)

SAMPLE_C = HotpotSample(
    id="c",
    subset="distractor",
    split="validation",
    question="Who wrote the novel Dune?",
    answer="Frank Herbert",
    type="bridge",
    level="easy",
    context_docs=[ContextDoc(title="Dune", sentences=["Dune is a 1965 novel by Frank Herbert."])],
    supporting_facts=[SupportingFact(title="Dune", sent_id=0)],
)


def test_cluster_records_groups_similar_questions_together():
    clusters = cluster_records([SAMPLE_A, SAMPLE_B, SAMPLE_C], similarity_threshold=0.3)

    assert len(clusters) == 2
    cluster_sizes = sorted(cluster["size"] for cluster in clusters)
    assert cluster_sizes == [1, 2]
    labels = " ".join(cluster["label"] for cluster in clusters).lower()
    assert "france" in labels or "capital" in labels
