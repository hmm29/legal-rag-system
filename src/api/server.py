# api_server.py
from fastapi import FastAPI, BackgroundTasks
from pydantic import BaseModel
import uvicorn
import asyncio

app = FastAPI(title="Legal RAG System API")

class Query(BaseModel):
    question: str

@app.post("/query")
async def query_endpoint(query: Query):
    result, latency = tracker.measure_latency(cached_query, query.question)
    return {
        "answer": result["result"],
        "sources": [doc.page_content for doc in result["source_documents"]],
        "latency": latency
    }

@app.get("/metrics")
async def metrics_endpoint():
    return tracker.generate_report()

# Run with: uvicorn api_server:app --reload
