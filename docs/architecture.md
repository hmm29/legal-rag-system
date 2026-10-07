# Architecture

This document describes what the code does today.

## Request path

```
client
  │  POST /query
  ▼
src/api/server.py        FastAPI routes, validation, error mapping
  ▼
src/api/handlers.py      request and response models, input cleaning
  ▼
src/service.py           RagService
  ├─ ResultCache         hit: return the stored answer
  ├─ RateLimiter         miss: wait for a slot
  ├─ RagPipeline         miss: retrieve and answer
  │    ├─ SentenceTransformerEmbedder   embed the question locally
  │    ├─ PineconeStore                 top-k passages by cosine similarity
  │    └─ OpenAIChat                    answer from the passages only
  └─ PerformanceTracker  record latency and cache hit or miss
```

## Ingestion path

```
scripts/ingest.py
  load_documents → chunk_documents → embed → PineconeStore.upsert
```

Documents are plain `.txt` files. Chunks are 1,000 characters with 200 characters of overlap by default, cut at a paragraph or sentence boundary when one is close. Each chunk is stored with its text and source file name as metadata, under the id `source#index`.

## Components

| Component | File | Notes |
|---|---|---|
| Settings | `src/config.py` | Read once from environment variables or `.env`. Fails early with a clear message if a key is missing. |
| Chunking | `src/data/data_preparation.py` | Pure Python, no framework. |
| Embeddings | `src/vector_store/pinecone_store.py` | `all-MiniLM-L6-v2` (384 dimensions) through sentence-transformers, run locally. |
| Vector store | `src/vector_store/pinecone_store.py` | Pinecone serverless index, cosine metric. |
| Pipeline | `src/rag/pipeline.py` | Builds a numbered-passage prompt and instructs the model to answer only from it. Returns without a model call when nothing is retrieved. |
| Cache | `src/optimization/caching.py` | One JSON file per question, keyed by a hash of the normalized text. No expiry. |
| Rate limiter | `src/optimization/rate_limiting.py` | Sliding one-second window, thread-safe, default 20 calls per second. Applies to cache misses only. |
| Batching | `src/optimization/batch_processing.py` | Thread pool, results returned in input order. |
| Metrics | `src/metrics/performance_tracker.py` | In-memory latency samples, cache counters and batch throughput. |

## Design choices

- **Direct SDK calls instead of an orchestration framework.** The pipeline is about 70 lines, and each step is visible and replaceable.
- **Dependencies passed in.** `RagPipeline` and `RagService` take their embedder, store, model, cache and limiter as arguments, so tests swap in fakes and run with no network or keys.
- **Handlers separate from FastAPI.** Endpoint logic is plain functions, tested on their own; `server.py` only wires routes.
- **Lazy construction.** The service is built on the first request, so importing the app needs no credentials.
- **Local embeddings.** Embedding costs nothing per query and keeps one fewer network call on the request path. The trade-off is a larger image and a slower cold start.

## Deployment

A `Dockerfile` and `docker-compose.yml` run a single container. There is no Kubernetes configuration, autoscaling, authentication or shared cache; a multi-instance deployment would need the cache, rate limiter and metrics moved to a shared store.

## Not built yet

- Retrieval and answer-quality evaluation against a labeled set
- Cache expiry and invalidation on re-ingest
- Authentication
- Support for PDF and other document formats
