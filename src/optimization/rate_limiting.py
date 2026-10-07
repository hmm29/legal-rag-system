"""Sliding-window rate limiter for calls to the paid upstream APIs."""
import threading
import time
from collections import deque


class RateLimiter:
    """Allow at most `max_calls_per_second` calls in any one-second window.

    `wait()` blocks until the caller may proceed. It is safe to call from
    several threads. `clock` and `sleep` can be replaced in tests.
    """

    def __init__(self, max_calls_per_second: int = 20, clock=time.monotonic, sleep=time.sleep):
        if max_calls_per_second <= 0:
            raise ValueError("max_calls_per_second must be positive")
        self.max_calls_per_second = max_calls_per_second
        self._clock = clock
        self._sleep = sleep
        self._calls: deque[float] = deque()
        self._lock = threading.Lock()

    def _drop_expired(self, now: float) -> None:
        while self._calls and now - self._calls[0] >= 1.0:
            self._calls.popleft()

    def wait(self) -> None:
        with self._lock:
            now = self._clock()
            self._drop_expired(now)
            if len(self._calls) >= self.max_calls_per_second:
                delay = 1.0 - (now - self._calls[0])
                if delay > 0:
                    self._sleep(delay)
                now = self._clock()
                self._drop_expired(now)
            self._calls.append(now)
