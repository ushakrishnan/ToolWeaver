"""
Redis Distributed Cache for ToolWeaver (Phase 7)

Supports multiple Redis deployment options:
- Local Docker (Windows/WSL)
- Azure Cache for Redis (Standard, Premium tiers)
- Redis Cloud
- Self-hosted Redis cluster

Features:
- Circuit breaker pattern with automatic fallback to file cache
- Connection pooling for high throughput
- Multi-tier caching strategy (catalog 24h, search 1h, embeddings 7d)
- Automatic reconnection with exponential backoff
- TLS support for Azure Redis
"""

import hashlib
import logging
import os
import pickle
import ssl
import time
from pathlib import Path
from typing import Any

try:
    import redis
    from redis.connection import ConnectionPool
    from redis.exceptions import ConnectionError as RedisConnectionError
    from redis.exceptions import RedisError
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    redis = None

logger = logging.getLogger(__name__)


class CircuitBreaker:
    """
    Circuit breaker to prevent hammering failed Redis connection.

    States:
    - CLOSED: Normal operation, requests go to Redis
    - OPEN: Redis failed, use fallback only
    - HALF_OPEN: Testing if Redis recovered
    """

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.failures = 0
        self.last_failure_time: float = 0.0
        self.state = "CLOSED"

    def call(self, func: Any, *args: Any, **kwargs: Any) -> Any:
        """Execute function with circuit breaker protection"""
        if self.state == "OPEN":
            # Check if we should try recovery
            if time.time() - self.last_failure_time > self.recovery_timeout:
                self.state = "HALF_OPEN"
                logger.info("Circuit breaker: Attempting recovery (HALF_OPEN)")
            else:
                raise RedisConnectionError("Circuit breaker OPEN")

        try:
            result = func(*args, **kwargs)
            if self.state == "HALF_OPEN":
                self.reset()
            return result
        except Exception as e:
            self.record_failure()
            raise e

    def record_failure(self) -> None:
        """Record a failure and potentially open circuit"""
        self.failures += 1
        self.last_failure_time = float(time.time())

        if self.failures >= self.failure_threshold:
            self.state = "OPEN"
            logger.warning(
                f"Circuit breaker OPEN after {self.failures} failures. "
                f"Will retry in {self.recovery_timeout}s"
            )

    def reset(self) -> None:
        """Reset circuit breaker to CLOSED state"""
        self.failures = 0
        self.state = "CLOSED"
        logger.info("Circuit breaker CLOSED - Redis connection recovered")


class RedisCache:
    """
    Distributed cache using Redis with automatic fallback to file cache.

    Supports:
    - Local Redis (Docker/WSL): redis://localhost:6379
    - Azure Cache for Redis: rediss://cache.redis.cache.windows.net:6380
    - Redis Cloud: rediss://endpoint:port

    Usage:
        # Local Redis
        cache = RedisCache(redis_url="redis://localhost:6379")

        # Azure Redis (with password)
        cache = RedisCache(
            redis_url="rediss://myapp.redis.cache.windows.net:6380",
            password="your-access-key",
            ssl=True
        )

        # Store/retrieve
        cache.set("key", data, ttl=3600)
        data = cache.get("key")
    """

    def __init__(
        self,
        redis_url: str | None = None,
        password: str | None = None,
        ssl: bool = False,
        cache_dir: Path | None = None,
        enable_fallback: bool = True,
        pool_size: int = 10
    ):
        """
        Initialize Redis cache with fallback to file cache.

        Args:
            redis_url: Redis URL (redis://host:port or rediss://host:port for TLS)
            password: Redis password (for Azure/Cloud)
            ssl: Enable SSL/TLS (for Azure Cache for Redis)
            cache_dir: Fallback file cache directory
            enable_fallback: Enable fallback to file cache on Redis failure
            pool_size: Connection pool size
        """
        env_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.redis_url: str = redis_url if redis_url is not None else env_url
        self.password = password or os.getenv("REDIS_PASSWORD")
        self.ssl = ssl or self.redis_url.startswith("rediss://")
        self.enable_fallback = enable_fallback

        # File cache fallback
        self.cache_dir = cache_dir or Path.home() / ".toolweaver" / "cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Redis client and connection pool
        self.client: redis.Redis | None = None
        self.pool: ConnectionPool | None = None
        self.redis_available = False

        # Circuit breaker
        self.circuit_breaker = CircuitBreaker(
            failure_threshold=5,
            recovery_timeout=60
        )

        if REDIS_AVAILABLE:
            self._init_redis_client(pool_size)
        else:
            logger.warning("redis package not installed, using file cache only")

    def _init_redis_client(self, pool_size: int) -> None:
        """Initialize Redis client with connection pooling"""
        try:
            # Build connection kwargs
            connection_kwargs = {
                "max_connections": pool_size,
                "socket_connect_timeout": 5,
                "socket_timeout": 5,
                "retry_on_timeout": True,
                "health_check_interval": 30
            }

            # Add SSL/TLS for Azure Redis
            if self.ssl:
                connection_kwargs["ssl"] = True
                connection_kwargs["ssl_cert_reqs"] = ssl.CERT_NONE  # Don't verify cert for development

            # Create connection pool
            self.pool = ConnectionPool.from_url(
                self.redis_url,
                password=self.password,
                decode_responses=False,  # Binary mode for pickle
                **connection_kwargs
            )

            # Create Redis client
            self.client = redis.Redis(connection_pool=self.pool)

            # Test connection
            self.client.ping()
            self.redis_available = True

            logger.info(f"Connected to Redis at {self.redis_url}")

        except Exception as e:
            logger.warning(f"Failed to connect to Redis: {e}")
            self.redis_available = False
            if not self.enable_fallback:
                raise
            logger.info("Will use file cache fallback")

    def get(self, key: str) -> Any | None:
        """
        Get value from cache.

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        # Try Redis first
        if self.redis_available and self.client is not None:
            try:
                value = self.circuit_breaker.call(self.client.get, key)
                if value is not None:
                    logger.debug(f"Redis cache HIT: {key}")
                    return pickle.loads(value)
                logger.debug(f"Redis cache MISS: {key}")
            except Exception as e:
                logger.warning(f"Redis get failed: {e}")
                self.redis_available = False

        # Fallback to file cache
        if self.enable_fallback:
            return self._file_get(key)

        return None

    def set(self, key: str, value: Any, ttl: int = 3600) -> bool:
        """
        Set value in cache with TTL.

        Args:
            key: Cache key
            value: Value to cache (must be picklable)
            ttl: Time to live in seconds

        Returns:
            True if successful
        """
        # Try Redis first
        if self.redis_available and self.client is not None:
            try:
                serialized = pickle.dumps(value)
                self.circuit_breaker.call(
                    self.client.setex,
                    key,
                    ttl,
                    serialized
                )
                logger.debug(f"Redis cache SET: {key} (TTL={ttl}s)")

                # Also write to file cache for redundancy
                if self.enable_fallback:
                    self._file_set(key, value, ttl)

                return True
            except Exception as e:
                logger.warning(f"Redis set failed: {e}")
                self.redis_available = False

        # Fallback to file cache
        if self.enable_fallback:
            return self._file_set(key, value, ttl)

        return False

    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        success = False

        # Delete from Redis
        if self.redis_available and self.client is not None:
            try:
                self.circuit_breaker.call(self.client.delete, key)
                success = True
            except Exception as e:
                logger.warning(f"Redis delete failed: {e}")

        # Delete from file cache
        if self.enable_fallback:
            self._file_delete(key)
            success = True

        return success

    def clear(self) -> bool:
        """Clear entire cache"""
        success = False

        # Clear Redis
        if self.redis_available and self.client is not None:
            try:
                self.circuit_breaker.call(self.client.flushdb)
                logger.info("Redis cache cleared")
                success = True
            except Exception as e:
                logger.warning(f"Redis clear failed: {e}")

        # Clear file cache
        if self.enable_fallback:
            for cache_file in self.cache_dir.glob("*"):
                cache_file.unlink()
            logger.info("File cache cleared")
            success = True

        return success

    def _file_get(self, key: str) -> Any | None:
        """Get from file cache"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "rb") as f:
                data = pickle.load(f)

            # Check expiration
            if data["expires_at"] < time.time():
                cache_file.unlink()
                return None

            logger.debug(f"File cache HIT: {key}")
            return data["value"]
        except Exception as e:
            logger.warning(f"File cache read failed: {e}")
            return None

    def _file_set(self, key: str, value: Any, ttl: int) -> bool:
        """Set in file cache"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"

        try:
            data = {
                "value": value,
                "expires_at": time.time() + ttl
            }
            with open(cache_file, "wb") as f:
                pickle.dump(data, f)
            logger.debug(f"File cache SET: {key}")
            return True
        except Exception as e:
            logger.warning(f"File cache write failed: {e}")
            return False

    def _file_delete(self, key: str) -> None:
        """Delete from file cache"""
        cache_file = self.cache_dir / f"{self._hash_key(key)}.cache"
        if cache_file.exists():
            cache_file.unlink()

    def _hash_key(self, key: str) -> str:
        """Hash key for filename"""
        return hashlib.sha256(key.encode()).hexdigest()[:16]

    def health_check(self) -> dict[str, Any]:
        """
        Check cache health status.

        Returns:
            Dict with status info
        """
        status = {
            "redis_available": self.redis_available,
            "redis_url": self.redis_url if self.redis_available else None,
            "circuit_breaker_state": self.circuit_breaker.state,
            "fallback_enabled": self.enable_fallback,
            "cache_dir": str(self.cache_dir) if self.enable_fallback else None
        }

        # Try ping if Redis available
        if self.redis_available and self.client is not None:
            try:
                self.circuit_breaker.call(self.client.ping)
                status["redis_ping"] = "OK"
            except Exception as e:
                status["redis_ping"] = f"FAILED: {e}"
                status["redis_available"] = False

        return status


class ToolCache:
    """
    High-level cache for ToolWeaver with multi-tier strategy.

    Cache Layers:
    1. Tool Catalog (24h TTL) - Full catalog snapshot
    2. Search Results (1h TTL) - Query results
    3. Embeddings (7d TTL) - Text embeddings
    4. Tool Metadata (24h TTL) - Individual tools
    """

    def __init__(self, redis_cache: RedisCache):
        self.cache = redis_cache

        # TTL values (seconds)
        self.CATALOG_TTL = 24 * 3600  # 24 hours
        self.SEARCH_TTL = 1 * 3600    # 1 hour
        self.EMBEDDING_TTL = 7 * 24 * 3600  # 7 days
        self.TOOL_TTL = 24 * 3600     # 24 hours

    def get_catalog(self, catalog_hash: str) -> dict | None:
        """Get cached tool catalog"""
        key = f"catalog:v2:{catalog_hash}"
        return self.cache.get(key)

    def set_catalog(self, catalog_hash: str, catalog_data: dict) -> bool:
        """Cache tool catalog"""
        key = f"catalog:v2:{catalog_hash}"
        return self.cache.set(key, catalog_data, ttl=self.CATALOG_TTL)

    def get_search_results(self, query_hash: str, catalog_version: str, top_k: int) -> list | None:
        """Get cached search results"""
        key = f"search:{query_hash}:{catalog_version}:{top_k}"
        return self.cache.get(key)

    def set_search_results(self, query_hash: str, catalog_version: str, top_k: int, results: list) -> bool:
        """Cache search results"""
        key = f"search:{query_hash}:{catalog_version}:{top_k}"
        return self.cache.set(key, results, ttl=self.SEARCH_TTL)

    def get_embedding(self, text_hash: str, model_name: str) -> Any:
        """Get cached embedding"""
        key = f"embedding:{text_hash}:{model_name}"
        return self.cache.get(key)

    def set_embedding(self, text_hash: str, model_name: str, embedding: Any) -> bool:
        """Cache embedding"""
        key = f"embedding:{text_hash}:{model_name}"
        return self.cache.set(key, embedding, ttl=self.EMBEDDING_TTL)

    def get_tool(self, tool_name: str, version: str) -> dict | None:
        """Get cached tool metadata"""
        key = f"tool:{tool_name}:v{version}"
        return self.cache.get(key)

    def set_tool(self, tool_name: str, version: str, tool_data: dict) -> bool:
        """Cache tool metadata"""
        key = f"tool:{tool_name}:v{version}"
        return self.cache.set(key, tool_data, ttl=self.TOOL_TTL)
