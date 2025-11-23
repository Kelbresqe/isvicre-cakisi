"""
Observability module for tool usage logging and statistics.
Provides centralized logging and metrics collection.
"""

import json
import logging
import time
from collections import defaultdict
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict

# Configure JSON logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("isvicre-cakisi")

# In-memory statistics for admin dashboard (Phase 6)
_stats = {
    "tool_calls": defaultdict(int),  # tool_slug -> count
    "successes": defaultdict(int),  # tool_slug -> count
    "errors": defaultdict(int),  # tool_slug -> count
    "cache_hits": defaultdict(int),  # tool_slug -> count
    "rate_limit_events": defaultdict(int),  # tool_slug -> count
    "total_duration_ms": defaultdict(float),  # tool_slug -> total ms
    "last_error": {},  # tool_slug -> error_detail
}

# v0.7.0: In-memory analytics store
_analytics = {
    "page_views": defaultdict(int),  # {tool_slug: count}
    "search_queries": [],  # List of search queries
    # v0.8.0: Tool flow tracking
    "tool_flows": [],  # List of (from_slug, to_slug) tuples
}


def log_tool_call(
    tool_slug: str,
    status: str,
    duration_ms: float,
    meta: Dict[str, Any] | None = None,
) -> None:
    """
    Log a tool call in JSON format.

    Args:
        tool_slug: Identifier of the tool (e.g., "image-converter")
        status: "success" or "error"
        duration_ms: Duration in milliseconds
        meta: Optional metadata like action, size, error message
    """
    log_data = {
        "tool": tool_slug,
        "status": status,
        "duration_ms": duration_ms,
    }

    if meta:
        log_data.update(meta)

    # Update in-memory stats
    _stats["tool_calls"][tool_slug] += 1
    _stats["total_duration_ms"][tool_slug] += duration_ms

    if meta and meta.get("cached"):
        _stats["cache_hits"][tool_slug] += 1

    if status == "success":
        _stats["successes"][tool_slug] += 1
        logger.info(f"Tool Call: {json.dumps(log_data)}")
    else:
        _stats["errors"][tool_slug] += 1
        _stats["last_error"][tool_slug] = log_data
        logger.error(f"Tool Error: {json.dumps(log_data)}")


def log_security_event(event_type: str, detail: Dict[str, Any] | None = None) -> None:
    """
    Log security-related events.

    Args:
        event_type: Type of security event (e.g., "invalid_file", "rate_limit")
        detail: Additional details about the event
    """
    log_data = {
        "event_type": event_type,
        "timestamp": datetime.now().isoformat(),
    }

    if detail:
        log_data.update(detail)
        # Track rate limits per tool if tool info is available
        if event_type == "rate_limit_exceeded" and "path" in detail:
            # Try to extract tool slug from path
            path = detail["path"]
            if "/tools/" in path:
                try:
                    tool_slug = path.split("/tools/")[1].split("/")[0]
                    _stats["rate_limit_events"][tool_slug] += 1
                except IndexError:
                    pass

    logger.warning(f"Security Event: {json.dumps(log_data)}")


@contextmanager
def track_tool_call(tool_slug: str, meta: Dict[str, Any] | None = None):
    """
    Context manager to automatically track tool call duration and status.

    Usage:
        with track_tool_call("image-converter", {"action": "convert"}):
            # Do work
            pass
    """
    start_time = time.time()
    exception_occurred = None

    try:
        yield
    except Exception as e:
        exception_occurred = e
        raise
    finally:
        duration_ms = (time.time() - start_time) * 1000
        status = "error" if exception_occurred else "success"

        call_meta = meta.copy() if meta else {}
        if exception_occurred:
            call_meta["error"] = str(exception_occurred)

        log_tool_call(tool_slug, status, duration_ms, call_meta)


def get_stats() -> Dict[str, Any]:
    """
    Get current statistics for admin dashboard.

    Returns:
        Dictionary with tool usage statistics
    """
    total_calls = sum(_stats["tool_calls"].values())
    total_errors = sum(_stats["errors"].values())
    total_cache_hits = sum(_stats["cache_hits"].values())
    total_rate_limits = sum(_stats["rate_limit_events"].values())

    # Calculate top 3 tools
    top_tools = sorted(_stats["tool_calls"].items(), key=lambda x: x[1], reverse=True)[:3]

    return {
        "total_calls": total_calls,
        "total_errors": total_errors,
        "total_cache_hits": total_cache_hits,
        "total_rate_limits": total_rate_limits,
        "error_rate": round(total_errors / total_calls * 100, 2) if total_calls > 0 else 0,
        "top_tools": [{"slug": slug, "calls": count} for slug, count in top_tools],
        "by_tool": {
            tool_slug: {
                "calls": _stats["tool_calls"][tool_slug],
                "successes": _stats["successes"][tool_slug],
                "errors": _stats["errors"][tool_slug],
                "cache_hits": _stats["cache_hits"][tool_slug],
                "rate_limits": _stats["rate_limit_events"][tool_slug],
                "avg_duration_ms": round(
                    _stats["total_duration_ms"][tool_slug] / _stats["tool_calls"][tool_slug],
                    2,
                )
                if _stats["tool_calls"][tool_slug] > 0
                else 0,
                "last_error": _stats["last_error"].get(tool_slug),
            }
            for tool_slug in _stats["tool_calls"].keys()
        },
    }


def reset_stats() -> None:
    """Reset statistics (useful for testing)."""
    global _stats
    _stats = {
        "tool_calls": defaultdict(int),
        "successes": defaultdict(int),
        "errors": defaultdict(int),
        "cache_hits": defaultdict(int),
        "rate_limit_events": defaultdict(int),
        "total_duration_ms": defaultdict(float),
        "last_error": {},
    }


# --- v0.7.0: Analytics Functions ---


def record_page_view(tool_slug: str, user_agent: str | None = None, referer: str | None = None) -> None:
    """
    Record a tool page view for analytics.

    Args:
        tool_slug: Tool identifier
        user_agent: Optional user agent string
        referer: Optional referer URL
    """
    _analytics["page_views"][tool_slug] += 1
    logger.debug(f"Page view recorded: {tool_slug}")


def record_search_query(query: str) -> None:
    """
    Record a search query for analytics.

    Args:
        query: Search query string (minimum 2 characters)
    """
    if len(query.strip()) >= 2:
        _analytics["search_queries"].append(query.strip())
        logger.debug(f"Search query recorded: {query}")


def get_analytics_stats() -> Dict[str, Any]:
    """
    Get analytics statistics for admin dashboard.

    Returns:
        Dictionary with page view and search query statistics
    """
    from collections import Counter

    total_page_views = sum(_analytics["page_views"].values())

    # Top 10 most viewed tools
    top_viewed = sorted(_analytics["page_views"].items(), key=lambda x: x[1], reverse=True)[:10]

    # Top 10 search queries
    query_counter = Counter(_analytics["search_queries"])
    top_searches = query_counter.most_common(10)

    return {
        "total_page_views": total_page_views,
        "total_searches": len(_analytics["search_queries"]),
        "unique_searches": len(query_counter),
        "top_viewed_tools": [{"slug": slug, "views": count} for slug, count in top_viewed],
        "top_searches": [{"query": query, "count": count} for query, count in top_searches],
        "page_views_by_tool": dict(_analytics["page_views"]),
        # v0.8.0: Flow statistics
        "top_flows": get_flow_stats()["top_flows"],
        "total_flows": len(_analytics["tool_flows"]),
    }


def record_tool_flow(from_tool_slug: str, to_tool_slug: str) -> None:
    """
    Record a tool-to-tool flow (v0.8.0).

    Args:
        from_tool_slug: Source tool slug
        to_tool_slug: Destination tool slug

    Used to track which tools users navigate between, helping
    identify common workflows and improve suggestions.
    """
    _analytics["tool_flows"].append((from_tool_slug, to_tool_slug))


def get_flow_stats() -> Dict[str, Any]:
    """
    Get tool flow statistics (v0.8.0).

    Returns:
        Dictionary with top tool flows and counts
    """
    from collections import Counter

    # Handle empty flows gracefully
    if not _analytics.get("tool_flows"):
        return {"top_flows": []}

    flow_counter = Counter(_analytics["tool_flows"])
    top_flows = flow_counter.most_common(10)

    return {
        "top_flows": [{"from": from_slug, "to": to_slug, "count": count} for (from_slug, to_slug), count in top_flows]
    }


def reset_analytics() -> None:
    """Reset analytics data (useful for testing)."""
    global _analytics
    _analytics = {
        "page_views": defaultdict(int),
        "search_queries": [],
        "tool_flows": [],  # v0.8.0
    }
