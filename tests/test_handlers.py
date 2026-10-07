from pydantic import ValidationError

from src.api.handlers import BatchRequest, QueryRequest, handle_batch, handle_metrics, handle_query
from src.rag.pipeline import RagPipeline
from src.service import RagService
from tests.fakes import FakeEmbedder, FakeLLM, FakeStore, raises


def make_service():
    return RagService(RagPipeline(FakeEmbedder(), FakeStore(), FakeLLM(), top_k=2))


def test_query_returns_answer_with_sources():
    response = handle_query(make_service(), QueryRequest(question="  What is an offer?  "))
    assert response.answer.startswith("A contract needs")
    assert response.sources[0].source == "contract.txt"
    assert response.cached is False


def test_batch_returns_one_result_per_question():
    response = handle_batch(make_service(), BatchRequest(questions=["a", "b", "c"]))
    assert len(response.results) == 3
    assert response.queries_per_second >= 0


def test_metrics_reports_what_was_served():
    service = make_service()
    handle_query(service, QueryRequest(question="q"))
    assert handle_metrics(service)["latency"]["count"] == 1


def test_blank_and_oversized_input_is_rejected():
    assert raises(ValidationError, QueryRequest, question="")
    assert raises(ValidationError, QueryRequest, question="x" * 2001)
    assert raises(ValidationError, BatchRequest, questions=[])
    assert raises(ValidationError, BatchRequest, questions=["q"] * 51)
    assert raises(ValueError, handle_query, make_service(), QueryRequest(question="   "))
    assert raises(ValueError, handle_batch, make_service(), BatchRequest(questions=["ok", "  "]))
