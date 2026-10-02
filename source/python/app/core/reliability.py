"""Retry + circuit breaker — stdlib only."""
import time, random
def backoff(attempt: int, base=0.5, cap=30.0):
    return min(cap, base * (2 ** attempt)) + random.uniform(0, base)
class CircuitBreaker:
    def __init__(self, threshold=5, reset_s=60.0):
        self.threshold = threshold; self.reset_s = reset_s
        self.failures = 0; self.opened_at = 0.0
    def before(self):
        if self.failures >= self.threshold:
            if time.time() - self.opened_at < self.reset_s: raise RuntimeError("circuit-open")
            self.failures = 0
    def after(self, ok: bool):
        if ok: self.failures = 0
        else:
            self.failures += 1
            if self.failures >= self.threshold: self.opened_at = time.time()
