# =============================================================================
# İsviçre Çakısı - Production Dockerfile
# Multi-stage build with security best practices (v0.9.0)
# =============================================================================

# -----------------------------------------------------------------------------
# Stage 1: Builder - Install dependencies
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS builder

# Install uv for fast dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock* ./

# Create virtual environment and install dependencies
# --no-dev: Skip dev dependencies for production
# --frozen: Use lockfile exactly
RUN uv venv /app/.venv && \
    uv sync --frozen --no-dev

# -----------------------------------------------------------------------------
# Stage 2: Runtime - Minimal production image
# -----------------------------------------------------------------------------
FROM python:3.13-slim AS runtime

# Security: Run as non-root user
RUN groupadd --gid 1000 appgroup && \
    useradd --uid 1000 --gid 1000 --shell /bin/bash --create-home appuser

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/app/.venv/bin:$PATH" \
    # Application settings
    ENV=prod \
    DEBUG=false \
    DOCS_ENABLED=false \
    REDOC_ENABLED=false

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --chown=appuser:appgroup app/ ./app/

# Create temp directory with correct permissions
RUN mkdir -p /app/temp && chown -R appuser:appgroup /app/temp

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Run the application
# Using uvicorn with production settings:
# --host 0.0.0.0: Listen on all interfaces
# --port 8000: Standard HTTP port
# --workers: Number of worker processes (adjust based on CPU)
# --access-log: Enable access logging
# --proxy-headers: Trust X-Forwarded-* headers from reverse proxy
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4", "--proxy-headers", "--access-log"]

# -----------------------------------------------------------------------------
# Build & Run Commands:
# -----------------------------------------------------------------------------
# Build:
#   docker build -t isvicre-cakisi:latest .
#
# Run:
#   docker run -d -p 8000:8000 --name isvicre-cakisi isvicre-cakisi:latest
#
# Run with environment override:
#   docker run -d -p 8000:8000 -e ENV=staging isvicre-cakisi:latest
#
# Development build (with dev dependencies):
#   docker build --target builder -t isvicre-cakisi:dev .
# -----------------------------------------------------------------------------
