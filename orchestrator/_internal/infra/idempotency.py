"""
Idempotency Keys for Agent Dispatch

Prevents duplicate agent operations during retries and concurrent execution.
Each dispatch task is assigned a unique idempotency key based on its content.

Threats Mitigated:
- AS-6: Race Conditions (duplicate operations on retry)
- Data corruption from concurrent dispatch
- Cost amplification from redundant agent calls
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any


@dataclass
class AgentTask:
    """
    Represents a task for agent dispatch with idempotency support.

    Attributes:
        agent_name: Name of the agent to invoke
        template: Prompt template string
        arguments: Dictionary of template arguments
        idempotency_key: Auto-generated unique key (hash of task content)
        max_retries: Maximum retry attempts allowed
        timeout: Task timeout in seconds
    """
    agent_name: str
    template: str
    arguments: dict[str, Any] = field(default_factory=dict)
    idempotency_key: str | None = field(default=None, init=False)
    max_retries: int = 3
    timeout: int = 300

    def __post_init__(self) -> None:
        """Generate idempotency key after initialization."""
        if self.idempotency_key is None:
            self.idempotency_key = generate_idempotency_key(
                self.agent_name,
                self.template,
                self.arguments
            )


def generate_idempotency_key(
    agent_name: str,
    template: str,
    arguments: dict[str, Any]
) -> str:
    """
    Generate idempotency key from task components.

    Creates a deterministic hash based on:
    - Agent name
    - Template string
    - Arguments (sorted for consistency)

    Args:
        agent_name: Name of agent to invoke
        template: Prompt template
        arguments: Template arguments

    Returns:
        16-character hex string (64 bits of SHA-256 hash)

    Example:
        >>> generate_idempotency_key("agent1", "Hello {name}", {"name": "Alice"})
        'a3f5c8d2e1b4f7a9'
    """
    # Create canonical representation
    canonical = {
        'agent': agent_name,
        'template': template,
        'arguments': arguments
    }

    # Serialize to JSON with sorted keys for consistency
    canonical_json = json.dumps(canonical, sort_keys=True, ensure_ascii=True)

    # Hash with SHA-256
    hash_obj = hashlib.sha256(canonical_json.encode('utf-8'))

    # Return first 16 hex characters (64 bits)
    return hash_obj.hexdigest()[:16]


@dataclass
class IdempotencyRecord:
    """
    Cache record for idempotent operations.

    Attributes:
        key: Idempotency key
        result: Cached result from previous execution
        created_at: Timestamp of cache entry
        expires_at: Expiration timestamp
        status: Execution status ('success', 'failed', 'pending')
    """
    key: str
    result: Any
    created_at: datetime
    expires_at: datetime
    status: str = 'success'

    def is_expired(self) -> bool:
        """Check if cache entry has expired."""
        return datetime.now() >= self.expires_at

    def is_valid(self) -> bool:
        """Check if cache entry is valid (not expired and successful)."""
        return not self.is_expired() and self.status == 'success'


class IdempotencyCache:
    """
    In-memory cache for idempotent operations.

    Stores results of agent dispatch operations to prevent duplicate execution.
    Entries expire after a configurable TTL to prevent unbounded memory growth.

    Usage:
        cache = IdempotencyCache(ttl_seconds=3600)

        # Check if task already executed
        if cache.has(task.idempotency_key):
            result = cache.get(task.idempotency_key)
            return result

        # Execute and store result
        result = execute_task(task)
        cache.store(task.idempotency_key, result)
    """

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize idempotency cache.

        Args:
            ttl_seconds: Time-to-live for cache entries (default: 1 hour)
        """
        self._cache: dict[str, IdempotencyRecord] = {}
        self._ttl_seconds = ttl_seconds

    def store(
        self,
        key: str,
        result: Any,
        status: str = 'success'
    ) -> None:
        """
        Store result in cache.

        Args:
            key: Idempotency key
            result: Result to cache
            status: Execution status
        """
        now = datetime.now()
        expires_at = now + timedelta(seconds=self._ttl_seconds)

        record = IdempotencyRecord(
            key=key,
            result=result,
            created_at=now,
            expires_at=expires_at,
            status=status
        )

        self._cache[key] = record

    def get(self, key: str) -> Any | None:
        """
        Get cached result.

        Args:
            key: Idempotency key

        Returns:
            Cached result if valid, None otherwise
        """
        record = self._cache.get(key)

        if record is None:
            return None

        # Check if expired
        if record.is_expired():
            del self._cache[key]
            return None

        # Only return successful results
        if record.status != 'success':
            return None

        return record.result

    def has(self, key: str) -> bool:
        """
        Check if valid cached result exists.

        Args:
            key: Idempotency key

        Returns:
            True if valid cache entry exists
        """
        return self.get(key) is not None

    def invalidate(self, key: str) -> None:
        """
        Remove entry from cache.

        Args:
            key: Idempotency key to invalidate
        """
        if key in self._cache:
            del self._cache[key]

    def clear(self) -> None:
        """Clear all cache entries."""
        self._cache.clear()

    def cleanup_expired(self) -> int:
        """
        Remove expired entries.

        Returns:
            Number of entries removed
        """
        now = datetime.now()
        expired_keys = [
            key for key, record in self._cache.items()
            if record.expires_at <= now
        ]

        for key in expired_keys:
            del self._cache[key]

        return len(expired_keys)

    def size(self) -> int:
        """Get current cache size."""
        return len(self._cache)

    def get_stats(self) -> dict[str, int]:
        """
        Get cache statistics.

        Returns:
            Dictionary with cache stats
        """
        total = len(self._cache)
        expired = sum(1 for r in self._cache.values() if r.is_expired())
        success = sum(1 for r in self._cache.values() if r.status == 'success')
        failed = sum(1 for r in self._cache.values() if r.status == 'failed')

        return {
            'total': total,
            'expired': expired,
            'success': success,
            'failed': failed,
            'valid': total - expired
        }


# Global cache instance for convenience
_global_cache = IdempotencyCache()


def get_global_cache() -> IdempotencyCache:
    """Get the global idempotency cache instance."""
    return _global_cache


def check_idempotency(key: str) -> Any | None:
    """
    Check global cache for cached result.

    Args:
        key: Idempotency key

    Returns:
        Cached result if available, None otherwise
    """
    return _global_cache.get(key)


def store_idempotent_result(
    key: str,
    result: Any,
    status: str = 'success'
) -> None:
    """
    Store result in global cache.

    Args:
        key: Idempotency key
        result: Result to store
        status: Execution status
    """
    _global_cache.store(key, result, status)
