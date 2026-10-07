"""End-to-end tests of the HTTP layer, using fakes in place of Pinecone and OpenAI."""
import pytest

pytest.importorskip("fastapi")
pytest.importorskip("httpx")

from fastapi.testclient import TestClient  # noqa: E402

from src.api.server import app, get_service  # noqa: E402
from src.rag.pipeline import RagPipeline  # noqa: E402
from src.service import RagService  # noqa: E402
from tests.fakes import FakeEmbedder, FakeLLM, FakeStore  # noqa: E402


@pytest.fixture()
def client():
    service = RagService(RagPipeline(FakeEmbedder(), FakeStore(), FakeLLM(), top_k=2))
    app.dependency_overrides[get_service] = lambda: service
    yield TestClient(app)
    app.dependency_overrides.clear()


def test_health(client):
    assert client.get("/health").json() == {"status": "ok"}


def test_query(client):
    response = client.post("/query", json={"question": "What is an offer?"})
    assert response.status_code == 200
    body = response.json()
    assert body["answer"].startswith("A contract needs")
    assert body["sources"][0]["source"] == "contract.txt"
    assert body["cached"] is False


def test_batch_query(client):
    response = client.post("/batch_query", json={"questions": ["a", "b"]})
    assert response.status_code == 200
    assert len(response.json()["results"]) == 2


def test_metrics_after_queries(client):
    client.post("/query", json={"question": "q"})
    assert client.get("/metrics").json()["latency"]["count"] == 1


def test_bad_requests_return_422(client):
    assert client.post("/query", json={"question": ""}).status_code == 422
    assert client.post("/query", json={"question": "   "}).status_code == 422
    assert client.post("/query", json={}).status_code == 422
    assert client.post("/batch_query", json={"questions": []}).status_code == 422
