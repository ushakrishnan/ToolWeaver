"""
Tests for Redis Distributed Cache (Phase 7)

Validates Redis caching with multiple deployment options:
- Local Docker/WSL fallback to file cache
- Azure Cache for Redis compatibility
- Circuit breaker behavior
"""

import os
import time

import pytest

from orchestrator._internal.infra.redis_cache import CircuitBreaker, RedisCache, ToolCache


@pytest.fixture
def temp_cache_dir(tmp_path):
    """Create temporary cache directory"""
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()
    return cache_dir


@pytest.fixture
def redis_cache_with_fallback(temp_cache_dir):
    """Redis cache with file fallback (works without Redis)"""
    return RedisCache(
        redis_url="redis://localhost:6379",
        cache_dir=temp_cache_dir,
        enable_fallback=True
    )


@pytest.fixture
def tool_cache(redis_cache_with_fallback):
    """High-level tool cache"""
    return ToolCache(redis_cache_with_fallback)


def test_redis_initialization(temp_cache_dir):
    """Test Redis cache initializes correctly"""
    cache = RedisCache(
        redis_url="redis://localhost:6379",
        cache_dir=temp_cache_dir,
        enable_fallback=True
    )

    assert cache.redis_url == "redis://localhost:6379"
    assert cache.enable_fallback == True
    assert cache.cache_dir == temp_cache_dir


def test_azure_redis_initialization(temp_cache_dir):
    """Test Azure Redis configuration"""
    cache = RedisCache(
        redis_url="rediss://test.redis.cache.windows.net:6380",
        password="test-key",
        ssl=True,
        cache_dir=temp_cache_dir,
        enable_fallback=True
    )

    assert cache.redis_url == "rediss://test.redis.cache.windows.net:6380"
    assert cache.ssl == True
    assert cache.password == "test-key"


def test_file_cache_fallback(redis_cache_with_fallback):
    """Test file cache fallback works when Redis unavailable"""
    # Set value (will use file cache since Redis likely unavailable)
    success = redis_cache_with_fallback.set("test_key", {"data": "value"}, ttl=60)
    assert success == True

    # Get value
    value = redis_cache_with_fallback.get("test_key")
    assert value == {"data": "value"}


def test_cache_expiration(redis_cache_with_fallback):
    """Test cache TTL expiration"""
    # Set with 1 second TTL
    redis_cache_with_fallback.set("expire_test", "data", ttl=1)

    # Should exist immediately
    value = redis_cache_with_fallback.get("expire_test")
    assert value == "data"

    # Wait for expiration
    time.sleep(2)

    # Should be expired
    value = redis_cache_with_fallback.get("expire_test")
    assert value is None


def test_cache_delete(redis_cache_with_fallback):
    """Test deleting cache entries"""
    # Set value
    redis_cache_with_fallback.set("delete_test", "data")
    assert redis_cache_with_fallback.get("delete_test") == "data"

    # Delete
    redis_cache_with_fallback.delete("delete_test")

    # Should be gone
    assert redis_cache_with_fallback.get("delete_test") is None


def test_cache_clear(redis_cache_with_fallback):
    """Test clearing entire cache"""
    # Set multiple values
    redis_cache_with_fallback.set("key1", "value1")
    redis_cache_with_fallback.set("key2", "value2")
    redis_cache_with_fallback.set("key3", "value3")

    # Clear all
    redis_cache_with_fallback.clear()

    # All should be gone
    assert redis_cache_with_fallback.get("key1") is None
    assert redis_cache_with_fallback.get("key2") is None
    assert redis_cache_with_fallback.get("key3") is None


def test_complex_data_types(redis_cache_with_fallback):
    """Test caching complex Python objects"""
    # List
    redis_cache_with_fallback.set("list", [1, 2, 3, 4, 5])
    assert redis_cache_with_fallback.get("list") == [1, 2, 3, 4, 5]

    # Dict
    redis_cache_with_fallback.set("dict", {"a": 1, "b": {"nested": 2}})
    assert redis_cache_with_fallback.get("dict") == {"a": 1, "b": {"nested": 2}}

    # Nested structure
    data = {
        "tools": [
            {"name": "tool1", "params": ["a", "b"]},
            {"name": "tool2", "params": ["c", "d"]}
        ],
        "metadata": {"version": "1.0"}
    }
    redis_cache_with_fallback.set("complex", data)
    assert redis_cache_with_fallback.get("complex") == data


def test_health_check(redis_cache_with_fallback):
    """Test health check returns status"""
    status = redis_cache_with_fallback.health_check()

    assert "redis_available" in status
    assert "circuit_breaker_state" in status
    assert "fallback_enabled" in status
    assert "cache_dir" in status

    assert status["fallback_enabled"] == True
    assert status["cache_dir"] is not None


def test_circuit_breaker():
    """Test circuit breaker opens after failures"""
    breaker = CircuitBreaker(failure_threshold=3, recovery_timeout=2)

    # Initially CLOSED
    assert breaker.state == "CLOSED"

    # Record failures
    for i in range(3):
        breaker.record_failure()

    # Should be OPEN now
    assert breaker.state == "OPEN"

    # Wait for recovery timeout
    time.sleep(3)

    # Should try recovery (will go to HALF_OPEN)
    def dummy_func():
        return "success"

    result = breaker.call(dummy_func)
    assert result == "success"
    assert breaker.state == "CLOSED"  # Successful call resets


def test_tool_cache_catalog(tool_cache):
    """Test caching tool catalogs"""
    catalog_data = {
        "tools": {
            "tool1": {"name": "tool1", "type": "function"},
            "tool2": {"name": "tool2", "type": "mcp"}
        },
        "version": "2.0"
    }

    # Cache catalog
    success = tool_cache.set_catalog("hash123", catalog_data)
    assert success == True

    # Retrieve catalog
    cached = tool_cache.get_catalog("hash123")
    assert cached == catalog_data


def test_tool_cache_search_results(tool_cache):
    """Test caching search results"""
    results = [
        ({"name": "github_create_pr", "score": 0.95}),
        ({"name": "github_list_issues", "score": 0.87})
    ]

    # Cache results
    success = tool_cache.set_search_results(
        query_hash="query123",
        catalog_version="v2",
        top_k=5,
        results=results
    )
    assert success == True

    # Retrieve results
    cached = tool_cache.get_search_results(
        query_hash="query123",
        catalog_version="v2",
        top_k=5
    )
    assert cached == results


def test_tool_cache_embeddings(tool_cache):
    """Test caching embeddings"""
    import numpy as np

    embedding = np.random.rand(384)  # 384-dim vector

    # Cache embedding
    success = tool_cache.set_embedding(
        text_hash="text123",
        model_name="all-MiniLM-L6-v2",
        embedding=embedding
    )
    assert success == True

    # Retrieve embedding
    cached = tool_cache.get_embedding(
        text_hash="text123",
        model_name="all-MiniLM-L6-v2"
    )

    assert cached is not None
    assert np.array_equal(cached, embedding)


def test_tool_cache_individual_tools(tool_cache):
    """Test caching individual tool metadata"""
    tool_data = {
        "name": "github_create_pr",
        "type": "function",
        "description": "Create GitHub pull request",
        "parameters": [{"name": "repo", "type": "string"}]
    }

    # Cache tool
    success = tool_cache.set_tool("github_create_pr", "1.0", tool_data)
    assert success == True

    # Retrieve tool
    cached = tool_cache.get_tool("github_create_pr", "1.0")
    assert cached == tool_data


def test_cache_hit_performance(redis_cache_with_fallback):
    """Test cache read performance"""
    # Warm up cache
    data = {"large_data": ["item"] * 1000}
    redis_cache_with_fallback.set("perf_test", data)

    # Measure read time
    iterations = 100
    start_time = time.time()

    for i in range(iterations):
        value = redis_cache_with_fallback.get("perf_test")
        assert value is not None

    elapsed_ms = (time.time() - start_time) * 1000
    avg_latency = elapsed_ms / iterations

    print("\nCache read performance:")
    print(f"  {iterations} reads in {elapsed_ms:.1f}ms")
    print(f"  Average latency: {avg_latency:.2f}ms per read")

    # Should be sub-millisecond for file cache
    assert avg_latency < 10, f"Cache too slow: {avg_latency:.2f}ms"


def test_ttl_layers(tool_cache):
    """Test different TTL values for cache layers"""
    # Catalog: 24h
    assert tool_cache.CATALOG_TTL == 24 * 3600

    # Search: 1h
    assert tool_cache.SEARCH_TTL == 1 * 3600

    # Embeddings: 7d
    assert tool_cache.EMBEDDING_TTL == 7 * 24 * 3600

    # Tools: 24h
    assert tool_cache.TOOL_TTL == 24 * 3600


def test_concurrent_access(redis_cache_with_fallback):
    """Test cache handles concurrent reads/writes"""
    import threading

    def writer(key, value):
        redis_cache_with_fallback.set(key, value)

    def reader(key):
        return redis_cache_with_fallback.get(key)

    # Create threads
    threads = []
    for i in range(10):
        t = threading.Thread(target=writer, args=(f"key_{i}", f"value_{i}"))
        threads.append(t)
        t.start()

    # Wait for all writes
    for t in threads:
        t.join()

    # Verify all values
    for i in range(10):
        value = redis_cache_with_fallback.get(f"key_{i}")
        assert value == f"value_{i}"


@pytest.mark.skipif(
    os.getenv("REDIS_URL") is None,
    reason="Redis not configured (set REDIS_URL env var to test)"
)
def test_real_redis_connection():
    """Test actual Redis connection (skip if not available)"""
    from orchestrator._internal.infra.redis_cache import REDIS_AVAILABLE

    if not REDIS_AVAILABLE:
        pytest.skip("redis package not installed")

    cache = RedisCache(
        redis_url=os.getenv("REDIS_URL"),
        password=os.getenv("REDIS_PASSWORD"),
        enable_fallback=False  # Fail if Redis unavailable
    )

    # Should connect successfully
    assert cache.redis_available == True

    # Test read/write
    cache.set("redis_test", "live_data")
    assert cache.get("redis_test") == "live_data"

    # Clean up
    cache.delete("redis_test")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
