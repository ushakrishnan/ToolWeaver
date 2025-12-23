"""
Tests for the token bucket rate limiter.
"""

import pytest
import asyncio
import time
from orchestrator._internal.infra.rate_limiter import RateLimiter


class TestRateLimiterBasics:
    """Test basic rate limiter functionality."""
    
    def test_initialization(self):
        """Test rate limiter initialization."""
        limiter = RateLimiter(requests_per_second=10.0)
        
        assert limiter.rate == 10.0
        assert limiter.burst_size == 20  # 2x default
        assert limiter.tokens == 20.0
    
    def test_custom_burst_size(self):
        """Test custom burst size configuration."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=50)
        
        assert limiter.burst_size == 50
        assert limiter.tokens == 50.0
    
    def test_invalid_rate(self):
        """Test that invalid rates raise ValueError."""
        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(requests_per_second=0)
        
        with pytest.raises(ValueError, match="must be positive"):
            RateLimiter(requests_per_second=-5.0)
    
    def test_repr(self):
        """Test string representation."""
        limiter = RateLimiter(10.0, 25)
        repr_str = repr(limiter)
        
        assert "10.0 req/s" in repr_str
        assert "burst=25" in repr_str


class TestRateEnforcement:
    """Test that rate limits are actually enforced."""
    
    @pytest.mark.asyncio
    async def test_sustained_rate_enforcement(self):
        """Test that sustained rate is enforced correctly."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=10)
        
        # Consume initial burst (10 tokens)
        for _ in range(10):
            await limiter.acquire()
        
        # Next 10 requests should take ~1 second (10 req/s)
        start = time.monotonic()
        for _ in range(10):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        
        # Should take ~1 second (with some tolerance for timing)
        assert 0.9 <= elapsed <= 1.2, f"Expected ~1s, got {elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_burst_capacity(self):
        """Test that burst capacity allows initial spike."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=20)
        
        # First 20 requests should happen immediately (burst)
        start = time.monotonic()
        for _ in range(20):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        
        # Should be nearly instant
        assert elapsed < 0.1, f"Burst should be instant, took {elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_wait_for_token_refill(self):
        """Test waiting for token refill after burst exhausted."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=10)
        
        # Exhaust burst
        for _ in range(10):
            await limiter.acquire()
        
        # 11th request should wait ~0.1s (1 token @ 10/s)
        start = time.monotonic()
        await limiter.acquire()
        elapsed = time.monotonic() - start
        
        assert 0.08 <= elapsed <= 0.15, f"Expected ~0.1s wait, got {elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_multiple_token_acquisition(self):
        """Test acquiring multiple tokens at once."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=20)
        
        # Acquire 5 tokens at once
        await limiter.acquire(tokens=5)
        
        # Should have 15 tokens left (20 - 5)
        available = limiter.get_available_tokens()
        assert 14.5 <= available <= 15.5


class TestContextManager:
    """Test context manager interface."""
    
    @pytest.mark.asyncio
    async def test_context_manager_basic(self):
        """Test basic context manager usage."""
        limiter = RateLimiter(requests_per_second=100.0)
        
        async with limiter:
            pass  # Should acquire and release
        
        # Should work multiple times
        async with limiter:
            pass
    
    @pytest.mark.asyncio
    async def test_context_manager_exception_handling(self):
        """Test that exceptions don't break rate limiter."""
        limiter = RateLimiter(requests_per_second=100.0)
        
        try:
            async with limiter:
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Should still work after exception
        async with limiter:
            pass


class TestConcurrentAccess:
    """Test thread safety under concurrent load."""
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self):
        """Test multiple concurrent tasks using same limiter."""
        limiter = RateLimiter(requests_per_second=50.0, burst_size=50)
        
        request_times = []
        
        async def make_request(request_id: int):
            async with limiter:
                request_times.append((request_id, time.monotonic()))
        
        # Launch 100 concurrent requests
        start = time.monotonic()
        await asyncio.gather(*[make_request(i) for i in range(100)])
        total_elapsed = time.monotonic() - start
        
        # Should have 100 requests
        assert len(request_times) == 100
        
        # Should take ~1-2 seconds (50 burst + 50 @ 50/s = 1s + overhead)
        assert 0.9 <= total_elapsed <= 2.5, f"Expected ~1-2s, got {total_elapsed:.2f}s"
    
    @pytest.mark.asyncio
    async def test_thread_safety(self):
        """Test that concurrent access doesn't corrupt state."""
        limiter = RateLimiter(requests_per_second=100.0, burst_size=100)
        
        async def rapid_acquire():
            for _ in range(20):
                await limiter.acquire()
        
        # Run 5 tasks concurrently (100 total acquires)
        await asyncio.gather(*[rapid_acquire() for _ in range(5)])
        
        # Tokens should be decremented correctly (100 burst - 100 used = 0)
        # (with small refill during execution)
        tokens = limiter.get_available_tokens()
        assert tokens <= 5, f"Expected near-zero tokens, got {tokens:.1f}"


class TestTokenRefill:
    """Test token bucket refill mechanics."""
    
    @pytest.mark.asyncio
    async def test_token_refill_over_time(self):
        """Test that tokens refill at correct rate."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=10)
        
        # Exhaust all tokens
        for _ in range(10):
            await limiter.acquire()
        
        # Wait 0.5 seconds (should refill 5 tokens @ 10/s)
        await asyncio.sleep(0.5)
        
        available = limiter.get_available_tokens()
        assert 4.0 <= available <= 6.0, f"Expected ~5 tokens, got {available:.1f}"
    
    @pytest.mark.asyncio
    async def test_refill_capped_at_burst_size(self):
        """Test that refill doesn't exceed burst size."""
        limiter = RateLimiter(requests_per_second=10.0, burst_size=10)
        
        # Wait long enough to refill beyond burst
        await asyncio.sleep(2.0)  # Would refill 20 tokens if uncapped
        
        available = limiter.get_available_tokens()
        assert available <= 10.5, f"Tokens should cap at 10, got {available:.1f}"


class TestEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.mark.asyncio
    async def test_acquire_zero_tokens(self):
        """Test that acquiring 0 tokens raises error."""
        limiter = RateLimiter(10.0)
        
        with pytest.raises(ValueError, match="must be positive"):
            await limiter.acquire(tokens=0)
    
    @pytest.mark.asyncio
    async def test_acquire_negative_tokens(self):
        """Test that acquiring negative tokens raises error."""
        limiter = RateLimiter(10.0)
        
        with pytest.raises(ValueError, match="must be positive"):
            await limiter.acquire(tokens=-5)
    
    @pytest.mark.asyncio
    async def test_very_high_rate(self):
        """Test limiter with very high rate (should not block)."""
        limiter = RateLimiter(requests_per_second=1000.0)
        
        # Should complete instantly even with many requests
        start = time.monotonic()
        for _ in range(100):
            await limiter.acquire()
        elapsed = time.monotonic() - start
        
        assert elapsed < 0.5, f"High rate should be fast, took {elapsed:.2f}s"
