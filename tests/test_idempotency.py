"""
Tests for Idempotency Keys and Caching

Validates prevention of duplicate operations and safe retry behavior.
"""

import time
from datetime import datetime, timedelta

import pytest

from orchestrator._internal.infra.idempotency import (
    AgentTask,
    IdempotencyCache,
    IdempotencyRecord,
    check_idempotency,
    generate_idempotency_key,
    get_global_cache,
    store_idempotent_result,
)


class TestIdempotencyKeyGeneration:
    """Test idempotency key generation."""

    def test_generate_key_deterministic(self):
        """Should generate same key for identical inputs."""
        key1 = generate_idempotency_key("agent1", "Hello {name}", {"name": "Alice"})
        key2 = generate_idempotency_key("agent1", "Hello {name}", {"name": "Alice"})
        assert key1 == key2

    def test_generate_key_different_agent(self):
        """Should generate different key for different agent."""
        key1 = generate_idempotency_key("agent1", "Hello", {})
        key2 = generate_idempotency_key("agent2", "Hello", {})
        assert key1 != key2

    def test_generate_key_different_template(self):
        """Should generate different key for different template."""
        key1 = generate_idempotency_key("agent1", "Hello", {})
        key2 = generate_idempotency_key("agent1", "Goodbye", {})
        assert key1 != key2

    def test_generate_key_different_arguments(self):
        """Should generate different key for different arguments."""
        key1 = generate_idempotency_key("agent1", "Hello {name}", {"name": "Alice"})
        key2 = generate_idempotency_key("agent1", "Hello {name}", {"name": "Bob"})
        assert key1 != key2

    def test_generate_key_argument_order_independent(self):
        """Should generate same key regardless of argument dict order."""
        key1 = generate_idempotency_key("agent1", "Test", {"a": 1, "b": 2, "c": 3})
        key2 = generate_idempotency_key("agent1", "Test", {"c": 3, "a": 1, "b": 2})
        assert key1 == key2

    def test_generate_key_format(self):
        """Should generate 16-character hex string."""
        key = generate_idempotency_key("agent1", "test", {})
        assert len(key) == 16
        assert all(c in '0123456789abcdef' for c in key)

    def test_generate_key_empty_args(self):
        """Should handle empty arguments."""
        key = generate_idempotency_key("agent1", "template", {})
        assert len(key) == 16

    def test_generate_key_complex_args(self):
        """Should handle complex nested arguments."""
        args = {
            "user": {"name": "Alice", "age": 30},
            "items": [1, 2, 3],
            "flag": True
        }
        key = generate_idempotency_key("agent1", "complex", args)
        assert len(key) == 16


class TestAgentTask:
    """Test AgentTask dataclass with auto-generated keys."""

    def test_task_auto_generates_key(self):
        """Should auto-generate idempotency key."""
        task = AgentTask(agent_name="agent1", template="Hello", arguments={})
        assert task.idempotency_key is not None
        assert len(task.idempotency_key) == 16

    def test_task_same_params_same_key(self):
        """Should generate same key for identical tasks."""
        task1 = AgentTask(agent_name="agent1", template="Hello", arguments={"name": "Alice"})
        task2 = AgentTask(agent_name="agent1", template="Hello", arguments={"name": "Alice"})
        assert task1.idempotency_key == task2.idempotency_key

    def test_task_different_params_different_key(self):
        """Should generate different keys for different tasks."""
        task1 = AgentTask(agent_name="agent1", template="Hello", arguments={"name": "Alice"})
        task2 = AgentTask(agent_name="agent1", template="Hello", arguments={"name": "Bob"})
        assert task1.idempotency_key != task2.idempotency_key

    def test_task_default_values(self):
        """Should have default values for optional fields."""
        task = AgentTask(agent_name="agent1", template="test")
        assert task.arguments == {}
        assert task.max_retries == 3
        assert task.timeout == 300


class TestIdempotencyRecord:
    """Test IdempotencyRecord."""

    def test_record_not_expired(self):
        """Should not be expired if within TTL."""
        now = datetime.now()
        expires = now + timedelta(hours=1)
        record = IdempotencyRecord(
            key="test",
            result={"data": "value"},
            created_at=now,
            expires_at=expires
        )
        assert not record.is_expired()
        assert record.is_valid()

    def test_record_expired(self):
        """Should be expired if past expiration time."""
        now = datetime.now()
        expires = now - timedelta(seconds=1)  # Already expired
        record = IdempotencyRecord(
            key="test",
            result={"data": "value"},
            created_at=now - timedelta(hours=2),
            expires_at=expires
        )
        assert record.is_expired()
        assert not record.is_valid()

    def test_record_failed_not_valid(self):
        """Should not be valid if status is failed."""
        now = datetime.now()
        expires = now + timedelta(hours=1)
        record = IdempotencyRecord(
            key="test",
            result=None,
            created_at=now,
            expires_at=expires,
            status='failed'
        )
        assert not record.is_expired()
        assert not record.is_valid()


class TestIdempotencyCache:
    """Test IdempotencyCache."""

    @pytest.fixture
    def cache(self):
        """Create a fresh cache for each test."""
        return IdempotencyCache(ttl_seconds=3600)

    def test_store_and_retrieve(self, cache):
        """Should store and retrieve results."""
        cache.store("key1", {"result": "success"})
        result = cache.get("key1")
        assert result == {"result": "success"}

    def test_has_returns_true_for_cached(self, cache):
        """Should return True for cached keys."""
        cache.store("key1", {"result": "success"})
        assert cache.has("key1")

    def test_has_returns_false_for_missing(self, cache):
        """Should return False for missing keys."""
        assert not cache.has("nonexistent")

    def test_get_returns_none_for_missing(self, cache):
        """Should return None for missing keys."""
        assert cache.get("nonexistent") is None

    def test_expired_entry_removed_on_get(self, cache):
        """Should remove expired entries when accessed."""
        # Create cache with 1-second TTL
        short_cache = IdempotencyCache(ttl_seconds=1)
        short_cache.store("key1", {"result": "success"})

        # Wait for expiration
        time.sleep(1.1)

        # Should return None and remove entry
        assert short_cache.get("key1") is None
        assert short_cache.size() == 0

    def test_failed_status_not_returned(self, cache):
        """Should not return results with failed status."""
        cache.store("key1", {"error": "failed"}, status='failed')
        assert cache.get("key1") is None

    def test_invalidate_removes_entry(self, cache):
        """Should remove entry on invalidation."""
        cache.store("key1", {"result": "success"})
        assert cache.has("key1")

        cache.invalidate("key1")
        assert not cache.has("key1")

    def test_clear_removes_all(self, cache):
        """Should remove all entries on clear."""
        cache.store("key1", {"result": "success"})
        cache.store("key2", {"result": "success"})
        assert cache.size() == 2

        cache.clear()
        assert cache.size() == 0

    def test_cleanup_expired(self, cache):
        """Should remove only expired entries."""
        # Create cache with short TTL
        short_cache = IdempotencyCache(ttl_seconds=1)

        # Store entries
        short_cache.store("key1", {"result": "1"})
        time.sleep(0.5)
        short_cache.store("key2", {"result": "2"})

        # Wait for first to expire
        time.sleep(0.7)  # Total: 1.2s for key1, 0.7s for key2

        # Cleanup
        removed = short_cache.cleanup_expired()
        assert removed == 1
        assert not short_cache.has("key1")
        assert short_cache.has("key2")

    def test_size(self, cache):
        """Should return correct size."""
        assert cache.size() == 0
        cache.store("key1", {"result": "1"})
        assert cache.size() == 1
        cache.store("key2", {"result": "2"})
        assert cache.size() == 2

    def test_get_stats(self, cache):
        """Should return cache statistics."""
        cache.store("key1", {"result": "1"}, status='success')
        cache.store("key2", {"result": "2"}, status='success')
        cache.store("key3", None, status='failed')

        stats = cache.get_stats()
        assert stats['total'] == 3
        assert stats['success'] == 2
        assert stats['failed'] == 1
        assert stats['valid'] == 3


class TestGlobalCache:
    """Test global cache helpers."""

    def test_get_global_cache(self):
        """Should return global cache instance."""
        cache = get_global_cache()
        assert isinstance(cache, IdempotencyCache)

    def test_check_idempotency_missing(self):
        """Should return None for missing key."""
        # Clean slate
        get_global_cache().clear()
        assert check_idempotency("missing") is None

    def test_store_and_check_idempotency(self):
        """Should store and retrieve from global cache."""
        get_global_cache().clear()

        store_idempotent_result("test_key", {"result": "success"})
        result = check_idempotency("test_key")
        assert result == {"result": "success"}

    def test_global_cache_persistence(self):
        """Should persist across function calls."""
        get_global_cache().clear()

        store_idempotent_result("persistent", {"data": "value"})

        # Access from different call
        cache = get_global_cache()
        assert cache.has("persistent")


class TestIntegration:
    """Test integration scenarios."""

    def test_prevent_duplicate_execution(self):
        """Should prevent duplicate task execution."""
        cache = IdempotencyCache()

        # First execution
        task = AgentTask(agent_name="agent1", template="Hello", arguments={})

        if not cache.has(task.idempotency_key):
            result = {"output": "Hello, World!"}  # Simulate execution
            cache.store(task.idempotency_key, result)

        # Second execution (should hit cache)
        task2 = AgentTask(agent_name="agent1", template="Hello", arguments={})
        assert cache.has(task2.idempotency_key)
        cached_result = cache.get(task2.idempotency_key)
        assert cached_result == {"output": "Hello, World!"}

    def test_retry_with_idempotency(self):
        """Should handle retries safely with idempotency."""
        cache = IdempotencyCache()

        task = AgentTask(agent_name="agent1", template="Retry test", arguments={})

        # First attempt fails
        cache.store(task.idempotency_key, None, status='failed')

        # Retry - should not get cached failed result
        assert not cache.has(task.idempotency_key)

        # Retry succeeds
        result = {"output": "Success"}
        cache.store(task.idempotency_key, result, status='success')

        # Next access gets successful result
        assert cache.get(task.idempotency_key) == result

    def test_concurrent_tasks_same_key(self):
        """Should handle concurrent tasks with same key."""
        cache = IdempotencyCache()

        task1 = AgentTask(agent_name="agent1", template="Concurrent", arguments={})
        task2 = AgentTask(agent_name="agent1", template="Concurrent", arguments={})

        # Both tasks have same key
        assert task1.idempotency_key == task2.idempotency_key

        # First task stores result
        cache.store(task1.idempotency_key, {"result": "done"})

        # Second task should get cached result
        assert cache.has(task2.idempotency_key)
        assert cache.get(task2.idempotency_key) == {"result": "done"}
