"""
Simple LRU cache for text-based tool results.
Caches deterministic operations (JSON, Base64, URL encoding).
"""

import hashlib
from collections import OrderedDict
from typing import Optional

from app.core.config import settings


class LRUCache:
    """
    Simple LRU (Least Recently Used) cache implementation.
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


# Global caches for each text tool
_text_tool_caches = {
    "json-formatter": LRUCache(max_size=getattr(settings, "TEXT_TOOL_CACHE_SIZE", 100)),
    "base64": LRUCache(max_size=getattr(settings, "TEXT_TOOL_CACHE_SIZE", 100)),
    "url-encoder": LRUCache(max_size=getattr(settings, "TEXT_TOOL_CACHE_SIZE", 100)),
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


def get_cached_result(tool_slug: str, input_text: str, **kwargs) -> Optional[str]:
    """
    Get cached result for text tool.

    Args:
        tool_slug: Tool identifier (e.g., "json-formatter")
        input_text: Input text
        **kwargs: Additional parameters

    Returns:
        Cached result or None if not found
    """
    if tool_slug not in _text_tool_caches:
        return None

    cache = _text_tool_caches[tool_slug]
    key = _generate_cache_key(tool_slug, input_text, **kwargs)

    return cache.get(key)


def set_cached_result(tool_slug: str, input_text: str, result: str, **kwargs) -> None:
    """
    Cache result for text tool.

    Args:
        tool_slug: Tool identifier
        input_text: Input text
        result: Result to cache
        **kwargs: Additional parameters
    """
    if tool_slug not in _text_tool_caches:
        return

    cache = _text_tool_caches[tool_slug]
    key = _generate_cache_key(tool_slug, input_text, **kwargs)

    cache.put(key, result)


def clear_cache(tool_slug: Optional[str] = None) -> None:
    """
    Clear cache for specific tool or all tools.

    Args:
        tool_slug: Tool to clear cache for, or None to clear all
    """
    if tool_slug and tool_slug in _text_tool_caches:
        _text_tool_caches[tool_slug].clear()
    elif tool_slug is None:
        for cache in _text_tool_caches.values():
            cache.clear()
