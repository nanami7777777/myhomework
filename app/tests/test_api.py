from fastapi.testclient import TestClient

from app.core.models import ContextDoc, HotpotSample, SupportingFact
from app.main import create_app


SAMPLE = HotpotSample(
    id="sample-1",
    subset="distractor",
    split="validation",
    question="Which magazine was started first Arthur's Magazine or First for Women?",
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


class FakeRepository:
    def search_samples(self, query: str, *, split=None, question_type=None, level=None, limit=10):
        return [{"id": SAMPLE.id, "question": SAMPLE.question, "score": 3.5, "type": SAMPLE.type, "level": SAMPLE.level}]

    def get_sample(self, sample_id: str):
        if sample_id == SAMPLE.id:
            return SAMPLE
        return None

    def get_stats(self):
        return {
            "total_samples": 1,
            "by_split": {"validation": 1},
            "by_type": {"comparison": 1},
            "by_level": {"medium": 1},
        }


client = TestClient(create_app(repository=FakeRepository()))


def test_health_endpoint_returns_ok():
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_search_endpoint_returns_search_results():
    response = client.get("/api/search", params={"q": "arthur magazine"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] == 1
    assert payload["results"][0]["id"] == SAMPLE.id


def test_sample_endpoint_returns_full_sample():
    response = client.get(f"/api/sample/{SAMPLE.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == SAMPLE.id
    assert payload["context_docs"][0]["title"] == "Arthur's Magazine"


def test_path_endpoint_returns_graph_payload():
    response = client.get(f"/api/path/{SAMPLE.id}")

    assert response.status_code == 200
    payload = response.json()
    assert payload["sample_id"] == SAMPLE.id
    assert len(payload["nodes"]) >= 4


def test_cluster_endpoint_returns_cluster_summary():
    response = client.get("/api/cluster", params={"q": "arthur"})

    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1
    assert payload["clusters"][0]["size"] >= 1


def test_stats_endpoint_returns_dashboard_stats():
    response = client.get("/api/stats")

    assert response.status_code == 200
    payload = response.json()
    assert payload["total_samples"] == 1
    assert payload["by_type"]["comparison"] == 1
