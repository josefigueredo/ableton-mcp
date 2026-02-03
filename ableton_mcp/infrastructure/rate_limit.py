"""Rate limiting for protecting against abuse.

Provides rate limiting implementations:
- Token bucket algorithm for smooth rate limiting
- Sliding window for request counting
- Per-client and global rate limits

Usage:
    limiter = TokenBucketRateLimiter(rate=10, capacity=20)

    if await limiter.acquire():
        # Process request
        pass
    else:
        # Rate limited - reject request
        pass
"""

from __future__ import annotations

import asyncio
import time
from abc import ABC, abstractmethod
from collections import defaultdict
from dataclasses import dataclass
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class RateLimitExceeded(Exception):
    """Exception raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded",
        retry_after: float | None = None,
    ) -> None:
        """Initialize rate limit exception.

        Args:
            message: Error message.
            retry_after: Seconds until the client can retry.
        """
        super().__init__(message)
        self.retry_after = retry_after


@dataclass
class RateLimitInfo:
    """Information about current rate limit status."""

    allowed: bool
    remaining: int
    limit: int
    reset_time: float
    retry_after: float | None = None

    def to_headers(self) -> dict[str, str]:
        """Convert to rate limit response headers.

        Returns:
            Dictionary of header name to value.
        """
        headers = {
            "X-RateLimit-Limit": str(self.limit),
            "X-RateLimit-Remaining": str(max(0, self.remaining)),
            "X-RateLimit-Reset": str(int(self.reset_time)),
        }
        if self.retry_after is not None:
            headers["Retry-After"] = str(int(self.retry_after))
        return headers


class RateLimiter(ABC):
    """Abstract base class for rate limiters."""

    @abstractmethod
    async def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitInfo:
        """Attempt to acquire tokens for a request.

        Args:
            key: Client identifier for per-client limiting.
            tokens: Number of tokens to acquire.

        Returns:
            RateLimitInfo with status and metadata.
        """
        pass

    @abstractmethod
    async def reset(self, key: str = "default") -> None:
        """Reset rate limit for a specific key.

        Args:
            key: Client identifier to reset.
        """
        pass


class TokenBucketRateLimiter(RateLimiter):
    """Token bucket rate limiter.

    Allows bursts up to capacity while maintaining a steady rate.
    Tokens are added at a constant rate up to the maximum capacity.
    """

    def __init__(
        self,
        rate: float = 10.0,
        capacity: int = 20,
    ) -> None:
        """Initialize token bucket rate limiter.

        Args:
            rate: Tokens added per second.
            capacity: Maximum tokens in the bucket.
        """
        self.rate = rate
        self.capacity = capacity
        self._buckets: dict[str, tuple[float, float]] = {}  # key -> (tokens, last_update)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitInfo:
        """Attempt to acquire tokens.

        Args:
            key: Client identifier.
            tokens: Number of tokens to acquire.

        Returns:
            RateLimitInfo with status.
        """
        async with self._lock:
            now = time.monotonic()

            # Get or initialize bucket
            if key in self._buckets:
                current_tokens, last_update = self._buckets[key]
            else:
                current_tokens = float(self.capacity)
                last_update = now

            # Add tokens based on elapsed time
            elapsed = now - last_update
            current_tokens = min(
                self.capacity,
                current_tokens + elapsed * self.rate,
            )

            # Check if we have enough tokens
            if current_tokens >= tokens:
                current_tokens -= tokens
                self._buckets[key] = (current_tokens, now)

                return RateLimitInfo(
                    allowed=True,
                    remaining=int(current_tokens),
                    limit=self.capacity,
                    reset_time=now + (self.capacity - current_tokens) / self.rate,
                )
            else:
                # Calculate retry time
                tokens_needed = tokens - current_tokens
                retry_after = tokens_needed / self.rate

                self._buckets[key] = (current_tokens, now)

                return RateLimitInfo(
                    allowed=False,
                    remaining=0,
                    limit=self.capacity,
                    reset_time=now + retry_after,
                    retry_after=retry_after,
                )

    async def reset(self, key: str = "default") -> None:
        """Reset bucket for a key.

        Args:
            key: Client identifier to reset.
        """
        async with self._lock:
            if key in self._buckets:
                del self._buckets[key]


class SlidingWindowRateLimiter(RateLimiter):
    """Sliding window rate limiter.

    Counts requests in a sliding time window.
    More strict than token bucket but simpler to understand.
    """

    def __init__(
        self,
        limit: int = 100,
        window_seconds: float = 60.0,
    ) -> None:
        """Initialize sliding window rate limiter.

        Args:
            limit: Maximum requests per window.
            window_seconds: Window duration in seconds.
        """
        self.limit = limit
        self.window_seconds = window_seconds
        self._requests: dict[str, list[float]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitInfo:
        """Attempt to make a request.

        Args:
            key: Client identifier.
            tokens: Number of requests (usually 1).

        Returns:
            RateLimitInfo with status.
        """
        async with self._lock:
            now = time.monotonic()
            window_start = now - self.window_seconds

            # Remove expired requests
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            current_count = len(self._requests[key])

            if current_count + tokens <= self.limit:
                # Add request timestamps
                for _ in range(tokens):
                    self._requests[key].append(now)

                return RateLimitInfo(
                    allowed=True,
                    remaining=self.limit - current_count - tokens,
                    limit=self.limit,
                    reset_time=now + self.window_seconds,
                )
            else:
                # Calculate when the oldest request will expire
                if self._requests[key]:
                    oldest = min(self._requests[key])
                    retry_after = oldest + self.window_seconds - now
                else:
                    retry_after = 0.0

                return RateLimitInfo(
                    allowed=False,
                    remaining=0,
                    limit=self.limit,
                    reset_time=now + self.window_seconds,
                    retry_after=max(0, retry_after),
                )

    async def reset(self, key: str = "default") -> None:
        """Reset requests for a key.

        Args:
            key: Client identifier to reset.
        """
        async with self._lock:
            if key in self._requests:
                del self._requests[key]


class ConcurrencyLimiter:
    """Limit concurrent operations.

    Uses a semaphore to limit the number of concurrent operations.
    Useful for protecting against resource exhaustion.
    """

    def __init__(self, max_concurrent: int = 10) -> None:
        """Initialize concurrency limiter.

        Args:
            max_concurrent: Maximum concurrent operations.
        """
        self.max_concurrent = max_concurrent
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._active = 0
        self._lock = asyncio.Lock()

    @property
    def active_count(self) -> int:
        """Get number of active operations."""
        return self._active

    @property
    def available(self) -> int:
        """Get number of available slots."""
        return self.max_concurrent - self._active

    async def acquire(self) -> bool:
        """Acquire a slot for an operation.

        Returns:
            True if slot acquired, False if would block.
        """
        try:
            # Try to acquire without blocking
            acquired = self._semaphore.locked() is False
            if acquired:
                await self._semaphore.acquire()
                async with self._lock:
                    self._active += 1
            return acquired
        except Exception:
            return False

    async def release(self) -> None:
        """Release a slot."""
        self._semaphore.release()
        async with self._lock:
            self._active = max(0, self._active - 1)

    async def __aenter__(self) -> ConcurrencyLimiter:
        """Async context manager entry."""
        await self._semaphore.acquire()
        async with self._lock:
            self._active += 1
        return self

    async def __aexit__(self, *args: Any) -> None:
        """Async context manager exit."""
        await self.release()


class CompositeRateLimiter(RateLimiter):
    """Combine multiple rate limiters.

    All limiters must allow the request for it to proceed.
    """

    def __init__(self, limiters: list[RateLimiter]) -> None:
        """Initialize composite rate limiter.

        Args:
            limiters: List of rate limiters to combine.
        """
        self.limiters = limiters

    async def acquire(self, key: str = "default", tokens: int = 1) -> RateLimitInfo:
        """Acquire from all limiters.

        Args:
            key: Client identifier.
            tokens: Number of tokens to acquire.

        Returns:
            RateLimitInfo with combined status.
        """
        results = []
        for limiter in self.limiters:
            result = await limiter.acquire(key, tokens)
            results.append(result)

            if not result.allowed:
                # Don't need to check other limiters
                return result

        # All limiters allowed
        if results:
            # Return the most restrictive remaining count
            min_remaining = min(r.remaining for r in results)
            min_limit = min(r.limit for r in results)
            max_reset = max(r.reset_time for r in results)

            return RateLimitInfo(
                allowed=True,
                remaining=min_remaining,
                limit=min_limit,
                reset_time=max_reset,
            )

        return RateLimitInfo(
            allowed=True,
            remaining=float("inf"),
            limit=0,
            reset_time=time.monotonic(),
        )

    async def reset(self, key: str = "default") -> None:
        """Reset all limiters for a key.

        Args:
            key: Client identifier to reset.
        """
        for limiter in self.limiters:
            await limiter.reset(key)


def create_default_rate_limiter() -> RateLimiter:
    """Create a default rate limiter configuration.

    Returns:
        Configured rate limiter suitable for most use cases.
    """
    return CompositeRateLimiter(
        [
            # Allow bursts but maintain steady rate
            TokenBucketRateLimiter(rate=10.0, capacity=20),
            # Hard limit per minute
            SlidingWindowRateLimiter(limit=100, window_seconds=60.0),
        ]
    )
