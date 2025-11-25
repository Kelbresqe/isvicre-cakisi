"""
Hybrid Cache Module (v1.0.0)

Provides caching with Redis as primary store and in-memory LRU as fallback.
Caches deterministic operations (JSON, Base64, URL encoding).
"""

import hashlib
from collections import OrderedDict
from typing import Optional

import structlog

from app.core.config import settings

logger = structlog.get_logger("cache")


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
    Used as fallback when Redis is unavailable.
    """

    def __init__(self, max_size: int = 100):
        self.cache: OrderedDict[str, str] = OrderedDict()
        self.max_size = max_size

    def get(self, key: str) -> Optional[str]:
        """Get value from cache, returns None if not found."""
        if key not in self.cache:
            return None

        # Move to end (most recently used)
        self.cache.move_to_end(key)
        return self.cache[key]

    def put(self, key: str, value: str) -> None:
        """Put value in cache, evicting oldest if necessary."""
        if key in self.cache:
            # Update existing
            self.cache.move_to_end(key)
        else:
            # Add new
            if len(self.cache) >= self.max_size:
                # Remove oldest (first item)
                self.cache.popitem(last=False)

        self.cache[key] = value

    def clear(self) -> None:
        """Clear all cached items."""
        self.cache.clear()

    def size(self) -> int:
        """Return current cache size."""
        return len(self.cache)


# Global in-memory caches for fallback
_text_tool_caches = {
    "json-formatter": LRUCache(max_size=settings.TEXT_TOOL_CACHE_SIZE),
    "base64": LRUCache(max_size=settings.TEXT_TOOL_CACHE_SIZE),
    "url-encoder": LRUCache(max_size=settings.TEXT_TOOL_CACHE_SIZE),
}


def _generate_cache_key(tool_slug: str, input_text: str, **kwargs) -> str:
    """
    Generate a cache key from input and options.

    Args:
        tool_slug: Tool identifier
        input_text: Input text
        **kwargs: Additional parameters (e.g., action, format)

    Returns:
        MD5 hash of the combined inputs
    """
    # Combine all inputs
    key_parts = [tool_slug, input_text]

    # Add sorted kwargs to ensure consistent keys
    for k in sorted(kwargs.keys()):
        key_parts.append(f"{k}={kwargs[k]}")

    combined = "|".join(str(p) for p in key_parts)

    # Hash for compact key
    return hashlib.md5(combined.encode()).hexdigest()


def _try_redis_get(cache_key: str) -> tuple[bool, Optional[str]]:
    """
    Try to get value from Redis.
    Returns (success, value) tuple.
    """
    try:
        from app.core.redis_client import redis_get

        value = redis_get(f"cache:{cache_key}")
        if value is not None:
            return True, value
        return True, None  # Redis available but key not found
    except Exception as e:
        logger.debug("redis_cache_get_failed", error=str(e))
        return False, None


def _try_redis_set(cache_key: str, value: str, ttl: int = 3600) -> bool:
    """
    Try to set value in Redis.
    Returns True if successful.
    """
    try:
        from app.core.redis_client import redis_set

        return redis_set(f"cache:{cache_key}", value, ttl=ttl)
    except Exception as e:
        logger.debug("redis_cache_set_failed", error=str(e))
        return False


def get_cached_result(tool_slug: str, input_text: str, **kwargs) -> Optional[str]:
    """
    Get cached result for text tool.
    Tries Redis first, falls back to in-memory cache.

    Args:
        tool_slug: Tool identifier (e.g., "json-formatter")
        input_text: Input text
        **kwargs: Additional parameters

    Returns:
        Cached result or None if not found
    """
    cache_key = _generate_cache_key(tool_slug, input_text, **kwargs)

    # Try Redis first
    redis_success, redis_value = _try_redis_get(cache_key)
    if redis_success and redis_value is not None:
        logger.debug("cache_hit", source="redis", tool=tool_slug)
        return redis_value

    # Fallback to in-memory
    if tool_slug in _text_tool_caches:
        memory_value = _text_tool_caches[tool_slug].get(cache_key)
        if memory_value is not None:
            logger.debug("cache_hit", source="memory", tool=tool_slug)
            return memory_value

    return None


def set_cached_result(tool_slug: str, input_text: str, result: str, **kwargs) -> None:
    """
    Cache result for text tool.
    Writes to both Redis and in-memory cache.

    Args:
        tool_slug: Tool identifier
        input_text: Input text
        result: Result to cache
        **kwargs: Additional parameters
    """
    cache_key = _generate_cache_key(tool_slug, input_text, **kwargs)

    # Try Redis
    redis_success = _try_redis_set(cache_key, result, ttl=settings.REDIS_TTL_SECONDS)
    if redis_success:
        logger.debug("cache_set", source="redis", tool=tool_slug)

    # Always write to in-memory as fallback
    if tool_slug in _text_tool_caches:
        _text_tool_caches[tool_slug].put(cache_key, result)
        if not redis_success:
            logger.debug("cache_set", source="memory", tool=tool_slug)


def clear_cache(tool_slug: Optional[str] = None) -> None:
    """
    Clear cache for specific tool or all tools.

    Args:
        tool_slug: Tool to clear cache for, or None to clear all
    """
    # Clear in-memory
    if tool_slug and tool_slug in _text_tool_caches:
        _text_tool_caches[tool_slug].clear()
    elif tool_slug is None:
        for cache in _text_tool_caches.values():
            cache.clear()

    # Clear Redis (pattern-based)
    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            if tool_slug:
                pattern = f"{settings.REDIS_KEY_PREFIX}cache:*{tool_slug}*"
            else:
                pattern = f"{settings.REDIS_KEY_PREFIX}cache:*"
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
                logger.info("cache_cleared", source="redis", count=len(keys))
    except Exception as e:
        logger.warning("redis_cache_clear_failed", error=str(e))


def get_cache_stats() -> dict:
    """
    Get cache statistics.

    Returns:
        Dictionary with cache stats
    """
    stats = {
        "memory": {tool: cache.size() for tool, cache in _text_tool_caches.items()},
        "redis": {"available": False, "keys": 0},
    }

    try:
        from app.core.redis_client import get_redis_client

        client = get_redis_client()
        if client:
            stats["redis"]["available"] = True
            pattern = f"{settings.REDIS_KEY_PREFIX}cache:*"
            stats["redis"]["keys"] = len(client.keys(pattern))
    except Exception:
        pass

    return stats
