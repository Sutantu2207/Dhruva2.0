"""Dhruva.AI V2 — Rate Limiting Foundation.

Provides brute-force and request flood protection using a sliding window algorithm.
Supports both Redis backends and high-performance in-memory fallback for local development and tests.
"""

import time
from collections import defaultdict
from typing import Dict, List, Optional
import threading


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding window rate limiter."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._requests: Dict[str, List[float]] = defaultdict(list)

    def is_rate_limited(self, key: str, max_requests: int, window_seconds: int = 60) -> bool:
        """Return True if key exceeds max_requests within window_seconds, False otherwise."""
        current_time = time.time()
        cutoff_time = current_time - window_seconds

        with self._lock:
            # Filter timestamps outside the sliding window
            timestamps = [ts for ts in self._requests[key] if ts > cutoff_time]
            if len(timestamps) >= max_requests:
                self._requests[key] = timestamps
                return True
            timestamps.append(current_time)
            self._requests[key] = timestamps
            return False

    def reset(self, key: Optional[str] = None) -> None:
        """Reset rate limit buckets."""
        with self._lock:
            if key:
                self._requests.pop(key, None)
            else:
                self._requests.clear()


# Global in-memory limiter instance
rate_limiter = InMemoryRateLimiter()
