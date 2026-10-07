"""Run one function over many inputs on a thread pool."""
import time
from concurrent.futures import ThreadPoolExecutor


def process_batch(fn, items: list, max_workers: int = 5) -> tuple[list, float]:
    """Apply `fn` to every item concurrently.

    Returns the results in the same order as `items`, and the wall-clock
    seconds the whole batch took.
    """
    if max_workers <= 0:
        raise ValueError("max_workers must be positive")
    start = time.perf_counter()
    if not items:
        return [], 0.0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(fn, items))
    return results, time.perf_counter() - start
