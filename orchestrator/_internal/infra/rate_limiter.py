"""
Token Bucket Rate Limiter for API Request Rate Control

Prevents overwhelming external APIs with parallel requests during multi-agent dispatch.
Uses the token bucket algorithm for smooth rate limiting with burst support.
"""

import asyncio
import time
from typing import Any


class RateLimiter:
    """
    Token bucket rate limiter for async operations.

    Features:
    - Smooth rate limiting (requests per second)
    - Burst capacity for temporary spikes
    - Thread-safe with asyncio.Lock
    - Context manager support

    Usage:
        rate_limiter = RateLimiter(requests_per_second=10.0, burst_size=20)

        # Option 1: Context manager
        async with rate_limiter:
            await make_api_call()

        # Option 2: Explicit acquire
        await rate_limiter.acquire()
        await make_api_call()

    Example:
        # Limit to 10 requests/second with burst of 20
        limiter = RateLimiter(10.0, 20)

        # These 20 requests happen immediately (burst)
        for _ in range(20):
            async with limiter:
                await api_call()

        # 21st request waits for token refill
        async with limiter:
            await api_call()  # Waits ~0.1s
    """

    def __init__(
        self,
        requests_per_second: float,
        burst_size: int | None = None,
    ):
        """
        Initialize rate limiter.

        Args:
            requests_per_second: Maximum sustained request rate
            burst_size: Maximum burst capacity (defaults to 2x rate)
        """
        if requests_per_second <= 0:
            raise ValueError("requests_per_second must be positive")

        self.rate = requests_per_second
        self.burst_size = burst_size or int(requests_per_second * 2)

        # Token bucket state
        self.tokens = float(self.burst_size)  # Start with full bucket
        self.last_refill = time.monotonic()

        # Thread safety
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        """
        Acquire tokens (blocks until available).

        Args:
            tokens: Number of tokens to acquire (default: 1)
        """
        if tokens <= 0:
            raise ValueError("tokens must be positive")

        while True:
            async with self._lock:
                # Refill tokens based on elapsed time
                now = time.monotonic()
                elapsed = now - self.last_refill
                refill_amount = elapsed * self.rate

                self.tokens = min(
                    self.burst_size,
                    self.tokens + refill_amount
                )
                self.last_refill = now

                # Check if enough tokens available
                if self.tokens >= tokens:
                    self.tokens -= tokens
                    return

                # Calculate wait time until next token
                tokens_needed = tokens - self.tokens
                wait_time = tokens_needed / self.rate

            # Wait outside the lock
            await asyncio.sleep(wait_time)

    async def __aenter__(self) -> "RateLimiter":
        """Context manager entry - acquire token."""
        await self.acquire()
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Context manager exit - nothing to do."""
        pass

    def get_available_tokens(self) -> float:
        """
        Get current available tokens (non-blocking check).

        Returns:
            Number of tokens currently available
        """
        now = time.monotonic()
        elapsed = now - self.last_refill
        refill_amount = elapsed * self.rate

        return min(
            self.burst_size,
            self.tokens + refill_amount
        )

    def __repr__(self) -> str:
        return (
            f"RateLimiter(rate={self.rate} req/s, "
            f"burst={self.burst_size}, "
            f"tokens={self.tokens:.1f})"
        )
