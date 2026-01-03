"""
Example 07: Caching and Optimization

Demonstrates:
- In-memory caching patterns
- Cache hit rate optimization
- Cost savings through caching
- Cache invalidation strategies

Use Case:
Improve performance and reduce costs through strategic caching
"""

import asyncio
import time
from collections import OrderedDict
from typing import Any

from orchestrator import mcp_tool

# ============================================================
# Simple Cache Implementation
# ============================================================

class SimpleCache:
    """In-memory cache with TTL support."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 3600):
        self.cache: OrderedDict[str, tuple[Any, float]] = OrderedDict()
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.hits = 0
        self.misses = 0

    def get(self, key: str) -> Any | None:
        """Get value from cache."""
        if key not in self.cache:
            self.misses += 1
            return None

        value, timestamp = self.cache[key]
        if time.time() - timestamp > self.ttl_seconds:
            del self.cache[key]
            self.misses += 1
            return None

        self.hits += 1
        self.cache.move_to_end(key)  # LRU
        return value

    def set(self, key: str, value: Any) -> None:
        """Set value in cache."""
        if key in self.cache:
            del self.cache[key]
        elif len(self.cache) >= self.max_size:
            self.cache.popitem(last=False)  # Remove oldest

        self.cache[key] = (value, time.time())

    def stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        total = self.hits + self.misses
        rate = (self.hits / total * 100) if total > 0 else 0
        return {
            "hits": self.hits,
            "misses": self.misses,
            "hit_rate": rate,
            "size": len(self.cache),
            "max_size": self.max_size
        }


# Global cache
cache = SimpleCache(max_size=100, ttl_seconds=3600)


# ============================================================
# Cached Tools
# ============================================================

@mcp_tool(domain="receipts", description="OCR with caching")
async def cached_ocr(image_uri: str) -> dict[str, Any]:
    """Extract text with caching."""
    cache_key = f"ocr:{image_uri}"

    # Check cache
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        cached = dict(cached)
        cached["cached"] = True
        return cached

    # Simulate processing
    await asyncio.sleep(0.8)

    result = {
        "text": "Receipt text extracted",
        "confidence": 0.98,
        "cached": False
    }

    cache.set(cache_key, result)
    return result


@mcp_tool(domain="parsing", description="Parse with caching")
async def cached_parse(text: str) -> dict[str, Any]:
    """Parse items with caching."""
    cache_key = f"parse:{text[:20]}"

    # Check cache
    cached = cache.get(cache_key)
    if isinstance(cached, dict):
        cached = dict(cached)
        cached["cached"] = True
        return cached

    # Simulate processing
    await asyncio.sleep(0.4)

    result = {
        "items": [{"name": "Item", "price": 10.0}],
        "count": 1,
        "cached": False
    }

    cache.set(cache_key, result)
    return result

    # Safety fallback for typing (unreachable)
    return {"cached": False}


# ============================================================
# Main Demo
# ============================================================

async def main() -> None:
    print("="*70)
    print("EXAMPLE 07: Caching & Optimization")
    print("="*70)
    print()

    print("Scenario 1: Without Caching")
    print("-" * 70)

    start_time = time.time()
    for _i in range(5):
        await asyncio.sleep(0.5)
    total_no_cache = time.time() - start_time

    print(f"  5 requests without cache: {total_no_cache:.2f}s")
    print()

    print("Scenario 2: With Caching (repeated requests)")
    print("-" * 70)

    times = []
    cache.hits = 0
    cache.misses = 0

    start_time = time.time()
    for i in range(10):
        # Alternate between 2 image URIs for cache hits
        image_uri = f"receipt_{i % 2}.jpg"
        start = time.time()
        result = await cached_ocr(image_uri)
        elapsed = time.time() - start
        times.append(elapsed)

        status = "HIT" if result.get("cached") else "MISS"
        print(f"  Request {i+1}: {elapsed*1000:.1f}ms ({status})")

    total_with_cache = time.time() - start_time
    print()

    print("Scenario 3: Multi-step Workflow with Caching")
    print("-" * 70)

    # Run same workflow twice
    for run in range(1, 3):
        print(f"\n  Run {run}:")
        times_run = []

        for _step in range(3):
            start = time.time()
            await cached_ocr("workflow.jpg")
            await cached_parse("test")
            elapsed = time.time() - start
            times_run.append(elapsed)

        run_time = sum(times_run)
        print(f"    Total time: {run_time:.2f}s")

    print()

    print("="*70)
    print("CACHING STATISTICS")
    print("="*70)

    stats = cache.stats()
    print()
    print(f"  Cache Hits:     {stats['hits']}")
    print(f"  Cache Misses:   {stats['misses']}")
    print(f"  Hit Rate:       {stats['hit_rate']:.1f}%")
    print(f"  Cache Size:     {stats['size']}/{stats['max_size']}")
    print()

    print("Performance Comparison:")
    print(f"  Without cache:  {total_no_cache:.2f}s")
    print(f"  With cache:     {total_with_cache:.2f}s")
    print(f"  Speedup:        {total_no_cache/total_with_cache:.2f}x")
    print(f"  Time saved:     {total_no_cache - total_with_cache:.2f}s")
    print()

    # Cost calculation
    cost_per_request = 0.052
    requests_no_cache = 5
    requests_with_cache = 10
    hit_rate = stats['hit_rate'] / 100

    cost_no = requests_no_cache * cost_per_request
    cost_yes = requests_with_cache * cost_per_request * (1 - hit_rate)
    savings = cost_no * requests_with_cache / requests_no_cache - cost_yes

    print("Cost Analysis:")
    print(f"  Cost without cache: ${cost_no:.4f} (5 requests)")
    print(f"  Cost with cache:    ${cost_yes:.4f} (10 requests, {stats['hit_rate']:.1f}% hit rate)")
    print(f"  Savings:            ${savings:.4f}")
    print()

    print("="*70)
    print("✓ Caching demonstration complete!")
    print("="*70)


if __name__ == "__main__":
    asyncio.run(main())
