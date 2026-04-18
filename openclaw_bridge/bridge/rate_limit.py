from __future__ import annotations

import time
from collections import deque


class RateLimiter:
    def __init__(self, rpm: int):
        self.rpm = max(1, rpm)
        self.window_seconds = 60
        self._hits: dict[str, deque[float]] = {}

    def allow(self, key: str) -> bool:
        now = time.time()
        bucket = self._hits.setdefault(key, deque())
        cutoff = now - self.window_seconds
        while bucket and bucket[0] < cutoff:
            bucket.popleft()
        if len(bucket) >= self.rpm:
            return False
        bucket.append(now)
        return True
