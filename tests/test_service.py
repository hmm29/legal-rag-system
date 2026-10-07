import tempfile

from src.metrics.performance_tracker import PerformanceTracker
from src.optimization.caching import ResultCache
from src.rag.pipeline import RagPipeline
from src.service import RagService
from tests.fakes import FakeEmbedder, FakeLLM, FakeStore


class CountingLimiter:
    def __init__(self):
        self.waits = 0

    def wait(self):
        self.waits += 1


def make_service(cache=None, limiter=None, llm=None):
    llm = llm or FakeLLM()
    pipeline = RagPipeline(FakeEmbedder(), FakeStore(), llm, top_k=2)
    return RagService(pipeline, cache=cache, limiter=limiter, batch_workers=3), llm


def test_answer_shape():
    service, _ = make_service()
    result = service.answer("What makes a contract valid?")
    assert result["answer"].startswith("A contract needs")
    assert result["sources"][0] == {
        "text": "An offer, acceptance and consideration.",
        "source": "contract.txt",
        "score": 0.9,
    }
    assert result["cached"] is False
    assert result["latency_ms"] >= 0


def test_second_identical_question_is_served_from_cache():
    with tempfile.TemporaryDirectory() as tmp:
        limiter = CountingLimiter()
        service, llm = make_service(cache=ResultCache(tmp), limiter=limiter)

        first = service.answer("What is an offer?")
        second = service.answer("what is an  offer?")

        assert (first["cached"], second["cached"]) == (False, True)
        assert second["answer"] == first["answer"]
        assert second["sources"] == first["sources"]
        assert len(llm.prompts) == 1
        assert limiter.waits == 1


def test_without_cache_every_call_hits_the_pipeline_and_limiter():
    limiter = CountingLimiter()
    service, llm = make_service(limiter=limiter)
    service.answer("q")
    service.answer("q")
    assert len(llm.prompts) == 2
    assert limiter.waits == 2


def test_batch_returns_results_in_order_with_throughput():
    service, _ = make_service()
    questions = [f"question {i}" for i in range(6)]
    batch = service.answer_batch(questions)
    assert len(batch["results"]) == 6
    assert all(result["cached"] is False for result in batch["results"])
    assert batch["duration_seconds"] >= 0
    assert batch["queries_per_second"] >= 0


def test_metrics_count_hits_misses_and_batches():
    with tempfile.TemporaryDirectory() as tmp:
        service, _ = make_service(cache=ResultCache(tmp))
        service.answer("a")
        service.answer("a")
        service.answer_batch(["b", "c"])
        report = service.metrics()
        assert report["latency"]["count"] == 4
        assert report["cache"] == {"hits": 1, "misses": 3}
        assert report["batches"]["count"] == 1


def test_empty_tracker_report_is_safe():
    report = PerformanceTracker().report()
    assert report["latency"] == {"count": 0}
    assert report["batches"]["mean_queries_per_second"] == 0.0


def test_tracker_percentiles():
    tracker = PerformanceTracker()
    for value in range(1, 101):
        tracker.record_latency(float(value))
    latency = tracker.report()["latency"]
    assert latency["mean_ms"] == 50.5
    assert latency["median_ms"] == 50.5
    assert 95 <= latency["p95_ms"] <= 96
    assert latency["max_ms"] == 100.0
