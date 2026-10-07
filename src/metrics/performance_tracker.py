"""Latency and throughput tracking for the running service."""
import threading

import numpy as np


class PerformanceTracker:
    def __init__(self):
        self._lock = threading.Lock()
        self._latencies_ms: list[float] = []
        self._cache_hits = 0
        self._cache_misses = 0
        self._batches: list[dict] = []

    def record_latency(self, latency_ms: float, cached: bool = False) -> None:
        with self._lock:
            self._latencies_ms.append(float(latency_ms))
            if cached:
                self._cache_hits += 1
            else:
                self._cache_misses += 1

    def record_batch(self, size: int, duration_seconds: float) -> float:
        throughput = size / duration_seconds if duration_seconds > 0 else 0.0
        with self._lock:
            self._batches.append(
                {"size": size, "duration_seconds": duration_seconds, "queries_per_second": throughput}
            )
        return throughput

    def report(self) -> dict:
        with self._lock:
            latencies = list(self._latencies_ms)
            batches = list(self._batches)
            hits, misses = self._cache_hits, self._cache_misses
        if latencies:
            latency = {
                "count": len(latencies),
                "mean_ms": round(float(np.mean(latencies)), 1),
                "median_ms": round(float(np.median(latencies)), 1),
                "p95_ms": round(float(np.percentile(latencies, 95)), 1),
                "p99_ms": round(float(np.percentile(latencies, 99)), 1),
                "max_ms": round(float(max(latencies)), 1),
            }
        else:
            latency = {"count": 0}
        throughputs = [b["queries_per_second"] for b in batches]
        return {
            "latency": latency,
            "cache": {"hits": hits, "misses": misses},
            "batches": {
                "count": len(batches),
                "mean_queries_per_second": round(float(np.mean(throughputs)), 1) if throughputs else 0.0,
            },
        }
