"""Example 07: Caching and Optimization"""
import asyncio
import time
from pathlib import Path
import sys

from orchestrator.redis_cache import RedisCache
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

async def main():
    print("="*70)
    print(" "*20 + "CACHING & OPTIMIZATION EXAMPLE")
    print("="*70)
    
    # Scenario 1: Without Cache
    print("\nScenario 1: Without Cache")
    print("-" * 40)
    times_no_cache = []
    for i in range(5):
        start = time.time()
        await asyncio.sleep(0.5)  # Simulate operation
        elapsed = time.time() - start
        times_no_cache.append(elapsed)
        print(f"  Request {i+1}: {elapsed:.3f}s")
    avg_no_cache = sum(times_no_cache) / len(times_no_cache)
    print(f"  Average: {avg_no_cache:.3f}s")
    
    # Scenario 2: With Cache
    print("\nScenario 2: With Redis Cache")
    print("-" * 40)
    try:
        cache = RedisCache(host="localhost", port=6379, ttl=3600)
        print("✓ Redis connected")
        
        times_with_cache = []
        for i in range(5):
            start = time.time()
            key = f"operation_{i % 2}"  # Repeat keys for cache hits
            
            result = await cache.get(key)
            if result is None:
                await asyncio.sleep(0.5)  # Simulate operation
                await cache.set(key, {"result": "data"})
                status = "miss"
            else:
                status = "hit"
            
            elapsed = time.time() - start
            times_with_cache.append(elapsed)
            print(f"  Request {i+1}: {elapsed:.3f}s (cache {status})")
        
        avg_with_cache = sum(times_with_cache) / len(times_with_cache)
        speedup = avg_no_cache / avg_with_cache if avg_with_cache > 0 else 0
        
        print(f"  Average: {avg_with_cache:.3f}s")
        print(f"  Speedup: {speedup:.1f}x faster")
        
    except Exception as e:
        print(f"⚠ Redis not available: {e}")
        print("  Install Redis: docker run -d -p 6379:6379 redis")
    
    # Cost Analysis
    print("\nCost Analysis:")
    print("-" * 40)
    print("  Without cache: $0.50 per request")
    print("  With cache: $0.05 per request (90% savings)")
    print("  Monthly (10K requests): $5,000 → $500")
    
    print("\n✓ Example completed!")

if __name__ == "__main__":
    asyncio.run(main())
