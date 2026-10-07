"""Request and response models, and the logic behind each endpoint.

Kept free of FastAPI so the logic can be tested without a running server.
"""
from pydantic import BaseModel, Field


class QueryRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)


class BatchRequest(BaseModel):
    questions: list[str] = Field(min_length=1, max_length=50)


class Source(BaseModel):
    text: str
    source: str
    score: float


class QueryResponse(BaseModel):
    answer: str
    sources: list[Source]
    cached: bool
    latency_ms: float


class BatchResponse(BaseModel):
    results: list[QueryResponse]
    duration_seconds: float
    queries_per_second: float


def _clean(question: str) -> str:
    cleaned = question.strip()
    if not cleaned:
        raise ValueError("question must not be blank")
    return cleaned


def handle_query(service, request: QueryRequest) -> QueryResponse:
    return QueryResponse(**service.answer(_clean(request.question)))


def handle_batch(service, request: BatchRequest) -> BatchResponse:
    questions = [_clean(question) for question in request.questions]
    return BatchResponse(**service.answer_batch(questions))


def handle_metrics(service) -> dict:
    return service.metrics()
