"""Ties the pipeline, cache, rate limiter and metrics into one service object."""
import time
from dataclasses import asdict

from src.metrics.performance_tracker import PerformanceTracker
from src.optimization.batch_processing import process_batch
from src.optimization.caching import ResultCache
from src.optimization.rate_limiting import RateLimiter


class RagService:
    """Answer questions, caching results and rate-limiting upstream calls.

    Cache hits return without touching the rate limiter, the vector store or
    the model. Only cache misses count against the rate limit, because those
    are the calls that cost money and hit third-party quotas.
    """

    def __init__(
        self,
        pipeline,
        cache: ResultCache | None = None,
        limiter: RateLimiter | None = None,
        tracker: PerformanceTracker | None = None,
        batch_workers: int = 5,
    ):
        self.pipeline = pipeline
        self.cache = cache
        self.limiter = limiter
        self.tracker = tracker or PerformanceTracker()
        self.batch_workers = batch_workers

    def answer(self, question: str) -> dict:
        start = time.perf_counter()
        result = self.cache.get(question) if self.cache else None
        cached = result is not None
        if not cached:
            if self.limiter:
                self.limiter.wait()
            answer = self.pipeline.answer(question)
            result = {
                "answer": answer.answer,
                "sources": [asdict(passage) for passage in answer.sources],
            }
            if self.cache:
                self.cache.set(question, result)
        latency_ms = (time.perf_counter() - start) * 1000
        self.tracker.record_latency(latency_ms, cached=cached)
        return {**result, "cached": cached, "latency_ms": round(latency_ms, 1)}

    def answer_batch(self, questions: list[str]) -> dict:
        results, duration = process_batch(self.answer, questions, max_workers=self.batch_workers)
        throughput = self.tracker.record_batch(len(questions), duration)
        return {
            "results": results,
            "duration_seconds": round(duration, 3),
            "queries_per_second": round(throughput, 1),
        }

    def metrics(self) -> dict:
        return self.tracker.report()


def build_service(settings=None, use_cache: bool = True) -> RagService:
    """Build the real service from environment settings."""
    from src.config import load_settings
    from src.rag.pipeline import OpenAIChat, RagPipeline
    from src.vector_store.pinecone_store import PineconeStore, SentenceTransformerEmbedder

    settings = settings or load_settings()
    store = PineconeStore(
        index_name=settings.index_name,
        dimension=settings.embedding_dim,
        api_key=settings.pinecone_api_key,
        cloud=settings.pinecone_cloud,
        region=settings.pinecone_region,
    )
    pipeline = RagPipeline(
        embedder=SentenceTransformerEmbedder(settings.embedding_model),
        store=store,
        llm=OpenAIChat(api_key=settings.openai_api_key, model=settings.chat_model),
        top_k=settings.top_k,
    )
    return RagService(
        pipeline=pipeline,
        cache=ResultCache(settings.cache_dir) if use_cache else None,
        limiter=RateLimiter(settings.max_qps),
        batch_workers=settings.batch_workers,
    )
