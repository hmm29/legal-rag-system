"""FastAPI app. Run with: uvicorn src.api.server:app --reload"""
from functools import lru_cache

from fastapi import Depends, FastAPI, HTTPException

from src.api.handlers import (
    BatchRequest,
    BatchResponse,
    QueryRequest,
    QueryResponse,
    handle_batch,
    handle_metrics,
    handle_query,
)

app = FastAPI(
    title="Legal RAG System",
    description="Ask a legal research question and get an answer with its source passages.",
)


@lru_cache(maxsize=1)
def get_service():
    """Build the service on first request, so importing this module needs no API keys."""
    from src.service import build_service

    return build_service()


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/query", response_model=QueryResponse)
def query(request: QueryRequest, service=Depends(get_service)) -> QueryResponse:
    try:
        return handle_query(service, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.post("/batch_query", response_model=BatchResponse)
def batch_query(request: BatchRequest, service=Depends(get_service)) -> BatchResponse:
    try:
        return handle_batch(service, request)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error


@app.get("/metrics")
def metrics(service=Depends(get_service)) -> dict:
    return handle_metrics(service)
