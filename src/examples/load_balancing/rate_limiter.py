"""
Rate Limiter Implementation

This module demonstrates different rate limiting algorithms:
1. Token Bucket
2. Fixed Window Counter
3. Sliding Window Log
"""

import time
from collections import deque
from dataclasses import dataclass
from typing import Dict, Deque
import redis
from datetime import datetime

@dataclass
class TokenBucket:
    """
    Token Bucket Algorithm Implementation
    
    Tokens are added to the bucket at a fixed rate, and each request consumes one token.
    If there are no tokens available, the request is rejected.
    
    ASCII Diagram:
    ```
    ┌─────────────────┐
    │                 │
    │  Token Bucket   │  ←── Tokens added at fixed rate
    │     ○○○○○       │
    │     ○○○○○       │
    └────────┬────────┘
             │
             ▼
        Requests consume tokens
    ```
    """
    capacity: int
    refill_rate: float
    tokens: float = 0.0
    last_refill: float = time.time()

    def allow_request(self) -> bool:
        now = time.time()
        # Refill tokens based on time elapsed
        elapsed = now - self.last_refill
        self.tokens = min(self.capacity, self.tokens + elapsed * self.refill_rate)
        self.last_refill = now

        if self.tokens >= 1:
            self.tokens -= 1
            return True
        return False


class FixedWindowCounter:
    """
    Fixed Window Counter Algorithm Implementation
    
    Requests are counted in fixed time windows. When the window expires,
    the counter resets.
    
    ASCII Diagram:
    ```
    Time ─────────────────────────────►
    
    ┌────────┐ ┌────────┐ ┌────────┐
    │Window 1│ │Window 2│ │Window 3│
    │Count: 5│ │Count: 3│ │Count: 0│
    └────────┘ └────────┘ └────────┘
    ```
    """
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.current_window = time.time() // window_size
        self.counter: Dict[int, int] = {}

    def allow_request(self) -> bool:
        current_window = int(time.time() // self.window_size)
        
        # Reset counter for new window
        if current_window > self.current_window:
            self.counter = {}
            self.current_window = current_window

        # Increment counter for current window
        self.counter[current_window] = self.counter.get(current_window, 0) + 1
        return self.counter[current_window] <= self.max_requests


class SlidingWindowLog:
    """
    Sliding Window Log Algorithm Implementation
    
    Maintains a log of request timestamps and removes old entries based on
    the window size.
    
    ASCII Diagram:
    ```
    Time ─────────────────────────────►
    
         Sliding Window
    ┌─────────────────────┐
    │   ●  ●●   ●  ●      │ ● = Request
    │                     │
    └─────────────────────┘
        Moves with time
    ```
    """
    def __init__(self, window_size: int, max_requests: int):
        self.window_size = window_size
        self.max_requests = max_requests
        self.request_log: Deque[float] = deque()

    def allow_request(self) -> bool:
        now = time.time()
        
        # Remove old requests outside the window
        while self.request_log and self.request_log[0] <= now - self.window_size:
            self.request_log.popleft()

        # Check if we can allow the request
        if len(self.request_log) < self.max_requests:
            self.request_log.append(now)
            return True
        return False


class RedisRateLimiter:
    """
    Distributed Rate Limiter using Redis
    
    Implements rate limiting using Redis for distributed systems.
    
    ASCII Diagram:
    ```
    ┌─────────┐    ┌─────────┐    ┌─────────┐
    │Service 1│    │Service 2│    │Service 3│
    └────┬────┘    └────┬────┘    └────┬────┘
         │              │              │
         └──────────────┼──────────────┘
                        │
                   ┌────▼────┐
                   │  Redis  │
                   └─────────┘
    ```
    """
    def __init__(self, redis_client: redis.Redis, key_prefix: str, window_size: int, max_requests: int):
        self.redis = redis_client
        self.key_prefix = key_prefix
        self.window_size = window_size
        self.max_requests = max_requests

    def allow_request(self, user_id: str) -> bool:
        key = f"{self.key_prefix}:{user_id}"
        pipe = self.redis.pipeline()
        
        now = datetime.now().timestamp()
        window_start = now - self.window_size
        
        # Remove old requests and add new one
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window_size)
        
        _, _, request_count, _ = pipe.execute()
        return request_count <= self.max_requests


# Example usage
if __name__ == "__main__":
    # Token Bucket Example
    limiter = TokenBucket(capacity=10, refill_rate=1)  # 10 tokens, 1 token/second
    print("Token Bucket:", limiter.allow_request())  # True

    # Fixed Window Counter Example
    window_limiter = FixedWindowCounter(window_size=60, max_requests=10)  # 10 requests per minute
    print("Fixed Window:", window_limiter.allow_request())  # True

    # Sliding Window Log Example
    sliding_limiter = SlidingWindowLog(window_size=60, max_requests=10)  # 10 requests per minute
    print("Sliding Window:", sliding_limiter.allow_request())  # True

    # Redis Rate Limiter Example (requires Redis server)
    try:
        redis_client = redis.Redis(host='localhost', port=6379, db=0)
        redis_limiter = RedisRateLimiter(
            redis_client=redis_client,
            key_prefix="rate_limit",
            window_size=60,
            max_requests=10
        )
        print("Redis Rate Limiter:", redis_limiter.allow_request("user123"))  # True
    except redis.ConnectionError:
        print("Redis server not available") 