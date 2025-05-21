# rate_limiting.py
import time
import threading
from queue import Queue

class RateLimiter:
    def __init__(self, max_calls_per_second=10):
        self.max_calls_per_second = max_calls_per_second
        self.call_timestamps = []
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if we've exceeded the rate limit"""
        with self.lock:
            now = time.time()
            
            # Remove timestamps older than 1 second
            self.call_timestamps = [ts for ts in self.call_timestamps if now - ts < 1.0]
            
            # If we've reached the limit, wait
            if len(self.call_timestamps) >= self.max_calls_per_second:
                sleep_time = 1.0 - (now - self.call_timestamps[0])
                if sleep_time > 0:
                    time.sleep(sleep_time)
                    now = time.time()  # Update the current time
            
            # Add the current timestamp
            self.call_timestamps.append(now)

# Initialize rate limiter
rate_limiter = RateLimiter(max_calls_per_second=20)

def query_with_rate_limit(question):
    rate_limiter.wait_if_needed()
    return qa(question)
