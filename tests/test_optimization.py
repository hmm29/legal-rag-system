import tempfile
import threading
import time

from src.optimization.batch_processing import process_batch
from src.optimization.caching import ResultCache
from src.optimization.rate_limiting import RateLimiter
from tests.fakes import raises


def test_cache_round_trip_and_miss():
    with tempfile.TemporaryDirectory() as tmp:
        cache = ResultCache(tmp)
        assert cache.get("What is consideration?") is None
        cache.set("What is consideration?", {"answer": "Something of value."})
        assert cache.get("What is consideration?") == {"answer": "Something of value."}


def test_cache_key_ignores_case_and_spacing():
    with tempfile.TemporaryDirectory() as tmp:
        cache = ResultCache(tmp)
        cache.set("What is  Consideration?", {"answer": "x"})
        assert cache.get("  what is consideration?  ") == {"answer": "x"}
        assert cache.get("What is an offer?") is None


def test_cache_survives_a_corrupt_file_and_clears():
    with tempfile.TemporaryDirectory() as tmp:
        cache = ResultCache(tmp)
        cache.set("q", {"answer": "a"})
        cache._path("q").write_text("{not json", encoding="utf-8")
        assert cache.get("q") is None
        assert cache.clear() == 1
        assert cache.clear() == 0


class FakeClock:
    def __init__(self):
        self.now = 0.0
        self.sleeps = []

    def clock(self):
        return self.now

    def sleep(self, seconds):
        self.sleeps.append(seconds)
        self.now += seconds


def test_rate_limiter_allows_calls_under_the_limit():
    fake = FakeClock()
    limiter = RateLimiter(3, clock=fake.clock, sleep=fake.sleep)
    for _ in range(3):
        limiter.wait()
    assert fake.sleeps == []


def test_rate_limiter_waits_when_the_window_is_full():
    fake = FakeClock()
    limiter = RateLimiter(2, clock=fake.clock, sleep=fake.sleep)
    limiter.wait()
    fake.now = 0.25
    limiter.wait()
    fake.now = 0.5
    limiter.wait()
    assert len(fake.sleeps) == 1
    assert abs(fake.sleeps[0] - 0.5) < 1e-9
    assert fake.now == 1.0


def test_rate_limiter_window_slides():
    fake = FakeClock()
    limiter = RateLimiter(1, clock=fake.clock, sleep=fake.sleep)
    limiter.wait()
    fake.now = 1.5
    limiter.wait()
    assert fake.sleeps == []


def test_rate_limiter_rejects_bad_limit():
    assert raises(ValueError, RateLimiter, 0)


def test_rate_limiter_is_thread_safe_with_a_real_clock():
    limiter = RateLimiter(50)
    stamps = []
    lock = threading.Lock()

    def worker():
        for _ in range(10):
            limiter.wait()
            with lock:
                stamps.append(time.monotonic())

    threads = [threading.Thread(target=worker) for _ in range(4)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join()
    assert len(stamps) == 40


def test_batch_keeps_input_order():
    def slow_double(n):
        time.sleep(0.01 * (5 - n))
        return n * 2

    results, duration = process_batch(slow_double, [1, 2, 3, 4], max_workers=4)
    assert results == [2, 4, 6, 8]
    assert duration > 0


def test_batch_runs_concurrently():
    def wait(_):
        time.sleep(0.05)
        return True

    _, duration = process_batch(wait, list(range(5)), max_workers=5)
    assert duration < 0.2


def test_batch_handles_empty_input_and_bad_workers():
    assert process_batch(lambda x: x, []) == ([], 0.0)
    assert raises(ValueError, process_batch, lambda x: x, [1], 0)
