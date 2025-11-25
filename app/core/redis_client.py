"""
Redis Client Module (v1.0.0)

Provides Redis connection with automatic fallback to in-memory storage.
Uses hiredis for performance optimization.
"""

from typing import Any

import structlog

from app.core.config import settings

logger = structlog.get_logger("redis")

# Redis client singleton
_redis_client: Any = None
_redis_available: bool = False


def get_redis_client():
    """
    Get Redis client with lazy initialization.
    Returns None if Redis is not available or disabled.
    """
    global _redis_client, _redis_available

    if not settings.REDIS_ENABLED:
        return None

    if _redis_client is not None:
        return _redis_client if _redis_available else None

    try:
        import redis

        _redis_client = redis.from_url(
            settings.REDIS_URL,
            decode_responses=True,
            socket_connect_timeout=2,
            socket_timeout=2,
            retry_on_timeout=True,
        )
        # Test connection
        _redis_client.ping()
        _redis_available = True
        logger.info("redis_connected", url=settings.REDIS_URL)
        return _redis_client
    except Exception as e:
        _redis_available = False
        logger.warning("redis_connection_failed", error=str(e), fallback="in-memory")
        return None


def is_redis_available() -> bool:
    """Check if Redis is available and connected."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.ping()
        return True
    except Exception:
        return False


def redis_get(key: str) -> str | None:
    """
    Get value from Redis with automatic key prefixing.
    Returns None if Redis is unavailable or key doesn't exist.
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.get(f"{settings.REDIS_KEY_PREFIX}{key}")
    except Exception as e:
        logger.error("redis_get_error", key=key, error=str(e))
        return None


def redis_set(key: str, value: str, ttl: int | None = None) -> bool:
    """
    Set value in Redis with automatic key prefixing.
    Returns False if Redis is unavailable.
    """
    client = get_redis_client()
    if client is None:
        return False
    try:
        full_key = f"{settings.REDIS_KEY_PREFIX}{key}"
        if ttl:
            client.setex(full_key, ttl, value)
        else:
            client.set(full_key, value)
        return True
    except Exception as e:
        logger.error("redis_set_error", key=key, error=str(e))
        return False


def redis_delete(key: str) -> bool:
    """Delete a key from Redis."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.delete(f"{settings.REDIS_KEY_PREFIX}{key}")
        return True
    except Exception as e:
        logger.error("redis_delete_error", key=key, error=str(e))
        return False


def redis_incr(key: str, amount: int = 1, ttl: int | None = None) -> int | None:
    """
    Increment a counter in Redis.
    Creates key with value `amount` if it doesn't exist.

    Args:
        key: The key to increment
        amount: Amount to increment by (default: 1)
        ttl: Optional TTL in seconds (only set on first increment)
    """
    client = get_redis_client()
    if client is None:
        return None
    try:
        full_key = f"{settings.REDIS_KEY_PREFIX}{key}"
        value = client.incrby(full_key, amount)
        if ttl and value == amount:  # Only set TTL on first increment
            client.expire(full_key, ttl)
        return value
    except Exception as e:
        logger.error("redis_incr_error", key=key, error=str(e))
        return None


def redis_lpush(key: str, value: str, max_length: int | None = None) -> bool:
    """Push value to a Redis list (left side)."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        full_key = f"{settings.REDIS_KEY_PREFIX}{key}"
        client.lpush(full_key, value)
        if max_length:
            client.ltrim(full_key, 0, max_length - 1)
        return True
    except Exception as e:
        logger.error("redis_lpush_error", key=key, error=str(e))
        return False


def redis_lrange(key: str, start: int = 0, end: int = -1) -> list[str]:
    """Get range of values from a Redis list."""
    client = get_redis_client()
    if client is None:
        return []
    try:
        return client.lrange(f"{settings.REDIS_KEY_PREFIX}{key}", start, end)
    except Exception as e:
        logger.error("redis_lrange_error", key=key, error=str(e))
        return []


def redis_hset(key: str, field: str, value: str) -> bool:
    """Set a hash field in Redis."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.hset(f"{settings.REDIS_KEY_PREFIX}{key}", field, value)
        return True
    except Exception as e:
        logger.error("redis_hset_error", key=key, error=str(e))
        return False


def redis_hget(key: str, field: str) -> str | None:
    """Get a hash field from Redis."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.hget(f"{settings.REDIS_KEY_PREFIX}{key}", field)
    except Exception as e:
        logger.error("redis_hget_error", key=key, error=str(e))
        return None


def redis_hgetall(key: str) -> dict[str, str]:
    """Get all hash fields from Redis."""
    client = get_redis_client()
    if client is None:
        return {}
    try:
        return client.hgetall(f"{settings.REDIS_KEY_PREFIX}{key}")
    except Exception as e:
        logger.error("redis_hgetall_error", key=key, error=str(e))
        return {}


def redis_hincrby(key: str, field: str, amount: int = 1) -> int | None:
    """Increment a hash field by amount."""
    client = get_redis_client()
    if client is None:
        return None
    try:
        return client.hincrby(f"{settings.REDIS_KEY_PREFIX}{key}", field, amount)
    except Exception as e:
        logger.error("redis_hincrby_error", key=key, error=str(e))
        return None


def redis_expire(key: str, ttl: int) -> bool:
    """Set TTL on a key."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        client.expire(f"{settings.REDIS_KEY_PREFIX}{key}", ttl)
        return True
    except Exception as e:
        logger.error("redis_expire_error", key=key, error=str(e))
        return False


def redis_keys(pattern: str) -> list[str]:
    """Get keys matching pattern (use with caution in production)."""
    client = get_redis_client()
    if client is None:
        return []
    try:
        full_pattern = f"{settings.REDIS_KEY_PREFIX}{pattern}"
        keys = client.keys(full_pattern)
        # Remove prefix from returned keys
        prefix_len = len(settings.REDIS_KEY_PREFIX)
        return [k[prefix_len:] for k in keys]
    except Exception as e:
        logger.error("redis_keys_error", pattern=pattern, error=str(e))
        return []


def redis_flush_prefix() -> bool:
    """Flush all keys with our prefix (careful in production!)."""
    client = get_redis_client()
    if client is None:
        return False
    try:
        keys = client.keys(f"{settings.REDIS_KEY_PREFIX}*")
        if keys:
            client.delete(*keys)
        return True
    except Exception as e:
        logger.error("redis_flush_error", error=str(e))
        return False
