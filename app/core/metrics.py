"""
Prometheus Metrics Module (v0.9.0)

Provides Prometheus-compatible metrics for monitoring and alerting.
Exposes /metrics endpoint for Prometheus scraping.
"""

from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, Info, generate_latest

from app.core.config import settings

# --- Application Info ---
APP_INFO = Info("isvicre_cakisi_app", "Application information")
APP_INFO.info(
    {
        "version": settings.VERSION,
        "environment": settings.ENV.value,
    }
)

# --- Request Metrics ---
REQUEST_COUNT = Counter(
    "isvicre_cakisi_requests_total",
    "Total number of requests",
    ["method", "endpoint", "status"],
)

REQUEST_LATENCY = Histogram(
    "isvicre_cakisi_request_latency_seconds",
    "Request latency in seconds",
    ["method", "endpoint"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0),
)

# --- Tool Metrics ---
TOOL_CALLS = Counter(
    "isvicre_cakisi_tool_calls_total",
    "Total tool API calls",
    ["tool_slug", "status"],
)

TOOL_LATENCY = Histogram(
    "isvicre_cakisi_tool_latency_seconds",
    "Tool processing latency in seconds",
    ["tool_slug"],
    buckets=(0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0, 30.0),
)

TOOL_FILE_SIZE = Histogram(
    "isvicre_cakisi_tool_file_size_bytes",
    "Uploaded file size in bytes",
    ["tool_slug"],
    buckets=(1024, 10240, 102400, 1048576, 5242880, 10485760, 26214400),  # 1KB to 25MB
)

# --- Cache Metrics ---
CACHE_HITS = Counter(
    "isvicre_cakisi_cache_hits_total",
    "Total cache hits",
    ["tool_slug"],
)

CACHE_MISSES = Counter(
    "isvicre_cakisi_cache_misses_total",
    "Total cache misses",
    ["tool_slug"],
)

# --- Rate Limit Metrics ---
RATE_LIMIT_HITS = Counter(
    "isvicre_cakisi_rate_limit_hits_total",
    "Total rate limit hits",
    ["tool_slug"],
)

# --- Security Metrics ---
SECURITY_EVENTS = Counter(
    "isvicre_cakisi_security_events_total",
    "Total security events",
    ["event_type"],
)


def record_request(method: str, endpoint: str, status: int, duration: float) -> None:
    """
    Record an HTTP request for Prometheus metrics.

    Args:
        method: HTTP method (GET, POST, etc.)
        endpoint: Request endpoint path
        status: HTTP status code
        duration: Request duration in seconds
    """
    # Normalize endpoint to avoid high cardinality
    normalized_endpoint = normalize_endpoint(endpoint)
    REQUEST_COUNT.labels(method=method, endpoint=normalized_endpoint, status=str(status)).inc()
    REQUEST_LATENCY.labels(method=method, endpoint=normalized_endpoint).observe(duration)


def record_tool_call(tool_slug: str, status: str, duration_seconds: float, file_size: int | None = None) -> None:
    """
    Record a tool API call for Prometheus metrics.

    Args:
        tool_slug: Tool identifier
        status: "success" or "error"
        duration_seconds: Processing duration in seconds
        file_size: Optional file size in bytes
    """
    TOOL_CALLS.labels(tool_slug=tool_slug, status=status).inc()
    TOOL_LATENCY.labels(tool_slug=tool_slug).observe(duration_seconds)
    if file_size is not None:
        TOOL_FILE_SIZE.labels(tool_slug=tool_slug).observe(file_size)


def record_cache_event(tool_slug: str, hit: bool) -> None:
    """
    Record a cache hit or miss.

    Args:
        tool_slug: Tool identifier
        hit: True if cache hit, False if miss
    """
    if hit:
        CACHE_HITS.labels(tool_slug=tool_slug).inc()
    else:
        CACHE_MISSES.labels(tool_slug=tool_slug).inc()


def record_rate_limit(tool_slug: str) -> None:
    """
    Record a rate limit event.

    Args:
        tool_slug: Tool identifier
    """
    RATE_LIMIT_HITS.labels(tool_slug=tool_slug).inc()


def record_security_event(event_type: str) -> None:
    """
    Record a security event.

    Args:
        event_type: Type of security event
    """
    SECURITY_EVENTS.labels(event_type=event_type).inc()


def normalize_endpoint(endpoint: str) -> str:
    """
    Normalize endpoint path to reduce cardinality.
    Replaces dynamic path segments with placeholders.

    Args:
        endpoint: Raw endpoint path

    Returns:
        Normalized endpoint path
    """
    # Remove query parameters
    endpoint = endpoint.split("?")[0]

    # Known tool paths - normalize to /tools/{slug}
    if endpoint.startswith("/tools/"):
        parts = endpoint.split("/")
        if len(parts) >= 3:
            tool_slug = parts[2]
            if len(parts) > 3:
                return f"/tools/{tool_slug}/action"
            return f"/tools/{tool_slug}"

    # Static files
    if endpoint.startswith("/static/"):
        return "/static/{file}"

    return endpoint


def get_metrics() -> bytes:
    """
    Generate Prometheus metrics output.

    Returns:
        Prometheus metrics in text format
    """
    return generate_latest()


def get_metrics_content_type() -> str:
    """
    Get content type for Prometheus metrics.

    Returns:
        Content type string
    """
    return CONTENT_TYPE_LATEST
