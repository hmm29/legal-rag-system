"""Measure latency and throughput against the live index and write the results.

Usage: python -m scripts.benchmark --questions benchmarks/questions.txt

Three passes over the same questions:
  1. Uncached, one at a time: latency of a full retrieve-and-answer call.
  2. Uncached, as one concurrent batch: throughput under the rate limit.
  3. Cached, one at a time: latency when the answer is already on disk.

Results depend on your machine, network, corpus and models, so the report
records all of them. Run it yourself before quoting any number.
"""
import argparse
import platform
import os
import tempfile
import time
from datetime import date
from pathlib import Path

import numpy as np

from src.config import load_settings
from src.optimization.caching import ResultCache
from src.service import build_service


def _stats(latencies_ms: list[float]) -> dict:
    return {
        "mean": float(np.mean(latencies_ms)),
        "median": float(np.median(latencies_ms)),
        "p95": float(np.percentile(latencies_ms, 95)),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--questions", default="benchmarks/questions.txt")
    parser.add_argument("--out", default="docs/performance_metrics.md")
    args = parser.parse_args()

    questions = [
        line.strip() for line in Path(args.questions).read_text(encoding="utf-8").splitlines() if line.strip()
    ]
    settings = load_settings()

    # Pass 1: uncached, sequential.
    service = build_service(settings, use_cache=False)
    service.answer(questions[0])  # warm up the embedding model and connections
    sequential = [service.answer(question)["latency_ms"] for question in questions]

    # Pass 2: uncached, one concurrent batch.
    batch = service.answer_batch(questions)

    # Pass 3: cached. Fill a fresh cache, then time the second read.
    with tempfile.TemporaryDirectory() as cache_dir:
        cached_service = build_service(settings, use_cache=False)
        cached_service.cache = ResultCache(cache_dir)
        for question in questions:
            cached_service.answer(question)
        cached = [cached_service.answer(question)["latency_ms"] for question in questions]

    vector_count = service.pipeline.store.count()
    seq, hit = _stats(sequential), _stats(cached)
    report = f"""# Performance metrics

Measured on {date.today().isoformat()} with `python -m scripts.benchmark`.

## Setup

| | |
|---|---|
| Machine | {platform.platform()}, {os.cpu_count()} CPUs |
| Python | {platform.python_version()} |
| Corpus | {vector_count} chunks in Pinecone index `{settings.index_name}` |
| Embedding model | {settings.embedding_model} (local) |
| Chat model | {settings.chat_model} |
| Questions | {len(questions)}, from `{args.questions}` |
| Rate limit | {settings.max_qps} uncached calls per second |
| Batch workers | {settings.batch_workers} |

## Results

| Pass | Mean | Median | p95 |
|---|---|---|---|
| Uncached, sequential | {seq['mean']:.0f} ms | {seq['median']:.0f} ms | {seq['p95']:.0f} ms |
| Cached, sequential | {hit['mean']:.1f} ms | {hit['median']:.1f} ms | {hit['p95']:.1f} ms |

Uncached batch of {len(questions)} questions: {batch['duration_seconds']:.2f} s, {batch['queries_per_second']:.1f} queries per second.

## How to read this

Uncached latency is dominated by the chat model's response time. Cached latency
is a local file read. Uncached throughput cannot exceed the rate limit.
"""
    Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
