# =============================================================================
# İsviçre Çakısı - Makefile
# v0.9.0 - Development & Deployment Shortcuts
# =============================================================================

.PHONY: help install dev test lint format typecheck clean docker docker-up docker-down docker-logs

# Default target
help:
	@echo "╔══════════════════════════════════════════════════════════════════╗"
	@echo "║           🇨🇭 İsviçre Çakısı - Available Commands                 ║"
	@echo "╠══════════════════════════════════════════════════════════════════╣"
	@echo "║ Development:                                                      ║"
	@echo "║   make install    - Install dependencies                          ║"
	@echo "║   make dev        - Start development server                      ║"
	@echo "║   make test       - Run tests                                     ║"
	@echo "║   make lint       - Run linter (ruff)                             ║"
	@echo "║   make format     - Format code (black)                           ║"
	@echo "║   make typecheck  - Run type checker (mypy)                       ║"
	@echo "║   make check      - Run all checks (lint + format + typecheck)    ║"
	@echo "╠══════════════════════════════════════════════════════════════════╣"
	@echo "║ Docker:                                                           ║"
	@echo "║   make docker     - Build Docker image                            ║"
	@echo "║   make docker-up  - Start Docker containers                       ║"
	@echo "║   make docker-down- Stop Docker containers                        ║"
	@echo "║   make docker-logs- View container logs                           ║"
	@echo "║   make docker-mon - Start with Grafana monitoring                 ║"
	@echo "╠══════════════════════════════════════════════════════════════════╣"
	@echo "║ Utilities:                                                        ║"
	@echo "║   make clean      - Clean temp files and caches                   ║"
	@echo "║   make sync       - Sync dependencies from lockfile               ║"
	@echo "║   make update     - Update dependencies                           ║"
	@echo "╚══════════════════════════════════════════════════════════════════╝"

# =============================================================================
# Development Commands
# =============================================================================

# Install dependencies
install:
	@echo "📦 Installing dependencies..."
	uv sync --frozen

# Start development server with auto-reload
dev:
	@echo "🚀 Starting development server..."
	uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Run tests
test:
	@echo "🧪 Running tests..."
	uv run pytest tests/ -v

# Run tests with coverage
test-cov:
	@echo "🧪 Running tests with coverage..."
	uv run pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Run linter
lint:
	@echo "🔍 Running linter..."
	uv run ruff check app/ tests/

# Run linter with auto-fix
lint-fix:
	@echo "🔧 Running linter with auto-fix..."
	uv run ruff check app/ tests/ --fix

# Format code
format:
	@echo "🎨 Formatting code..."
	uv run black app/ tests/

# Check formatting without modifying
format-check:
	@echo "🎨 Checking code formatting..."
	uv run black --check app/ tests/

# Run type checker
typecheck:
	@echo "📝 Running type checker..."
	uv run mypy app/ --ignore-missing-imports

# Run all checks
check: lint format-check typecheck
	@echo "✅ All checks passed!"

# =============================================================================
# Docker Commands
# =============================================================================

# Build Docker image
docker:
	@echo "🐳 Building Docker image..."
	docker build -t isvicre-cakisi:latest .

# Start Docker containers
docker-up:
	@echo "🐳 Starting Docker containers..."
	docker compose up -d

# Start Docker containers with build
docker-up-build:
	@echo "🐳 Building and starting Docker containers..."
	docker compose up -d --build

# Stop Docker containers
docker-down:
	@echo "🛑 Stopping Docker containers..."
	docker compose down

# View container logs
docker-logs:
	@echo "📋 Viewing container logs..."
	docker compose logs -f app

# Start with full monitoring stack (including Grafana)
docker-mon:
	@echo "📊 Starting with monitoring stack..."
	docker compose --profile monitoring up -d

# Remove all Docker artifacts
docker-clean:
	@echo "🧹 Cleaning Docker artifacts..."
	docker compose down -v --rmi local

# =============================================================================
# Utility Commands
# =============================================================================

# Clean temp files and caches
clean:
	@echo "🧹 Cleaning temp files and caches..."
	rm -rf temp/*
	rm -rf __pycache__
	rm -rf app/__pycache__
	rm -rf app/**/__pycache__
	rm -rf tests/__pycache__
	rm -rf .pytest_cache
	rm -rf .ruff_cache
	rm -rf .mypy_cache
	rm -rf htmlcov
	rm -rf .coverage
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	@echo "✅ Cleaned!"

# Sync dependencies from lockfile
sync:
	@echo "📦 Syncing dependencies..."
	uv sync --frozen

# Update dependencies
update:
	@echo "📦 Updating dependencies..."
	uv lock --upgrade
	uv sync

# Add a new dependency
add:
	@echo "Usage: make add pkg=<package_name>"
	@test -n "$(pkg)" && uv add $(pkg) || echo "Error: Please specify pkg=<package_name>"

# Add a new dev dependency
add-dev:
	@echo "Usage: make add-dev pkg=<package_name>"
	@test -n "$(pkg)" && uv add --dev $(pkg) || echo "Error: Please specify pkg=<package_name>"

# =============================================================================
# Production Commands
# =============================================================================

# Start production server
prod:
	@echo "🚀 Starting production server..."
	ENV=prod uv run uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4

# Health check
health:
	@curl -s http://localhost:8000/health | python -m json.tool

# Readiness check
ready:
	@curl -s http://localhost:8000/ready | python -m json.tool

# =============================================================================
# Version: 0.9.0
# =============================================================================
