# Changelog

## [1.1.0] - 2025-11-25

### 🎨 Phase 7A - New Tools & Design

#### New Tools

- **Dice Roller** (`app/tools/dice_roller`):
  - Advanced dice rolling with D4-D100 support
  - Custom notation parser (e.g., "2d6+3", "4d6kh3")
  - Advantage/Disadvantage mechanics
  - Roll history and animated results
- **Hash Generator** (`app/tools/hash_generator`):
  - Text and file hashing support
  - Algorithms: MD5, SHA-1, SHA-256, SHA-512, BLAKE2b
  - Hash comparison tool
  - File integrity verification
- **Color Picker** (`app/tools/color_picker`):
  - Advanced color conversion (HEX, RGB, HSL, CMYK)
  - Visual color picker and palette generation
  - Complementary, Analogous, Monochromatic schemes
  - Contrast checking
- **Lorem Ipsum Generator** (`app/tools/lorem_ipsum`):
  - Paragraph, sentence, and word generation
  - HTML tag support (<p>)
  - "Start with Lorem ipsum" option
- **Base Converter** (`app/tools/base_converter`):
  - Number base conversion (Binary, Octal, Decimal, Hex)
  - Real-time conversion to all bases
  - Large number support

#### Improvements

- **Core**: Added `MAX_UPLOAD_SIZE_MB` to settings for general file uploads
- **Templates**: Added `tojson` filter for better JS integration
- **Registry**: Added `DESIGN` category for design-related tools

## [1.0.0] - 2025-11-25

### 🚀 Redis Integration - Scalability Release

#### Major Features

- **Redis Backend**: Full Redis integration for distributed deployments
  - Automatic fallback to in-memory when Redis unavailable
  - Zero-downtime deployment support
  - Configurable via environment variables
- **Redis-Backed Caching**: `app/core/cache.py`
  - Hybrid cache: Redis primary + in-memory fallback
  - LRU eviction in memory, TTL-based in Redis
  - Tool-specific cache isolation
- **Distributed Rate Limiting**: `app/core/rate_limit.py`
  - Per-IP request counting across instances
  - Upload limit tracking with Redis persistence
  - Seamless in-memory fallback
- **Redis Health Checks**: `app/core/health.py`
  - Redis status in `/health` endpoint
  - Graceful degradation (healthy even if Redis unavailable)
  - Redis version and connection info

#### Infrastructure

- **Docker Compose Updates**:
  - Redis 7 Alpine service with health checks
  - App depends on Redis with graceful startup
  - Named volume for Redis persistence
  - Configurable Redis settings via environment
- **New Module**: `app/core/redis_client.py`
  - Lazy connection initialization
  - Auto key prefixing (configurable)
  - Full operation set: get/set/delete/incr/lpush/hset/hgetall/expire
  - Connection pooling with hiredis optimization

#### Configuration

New environment variables:

- `REDIS_ENABLED`: Enable/disable Redis (default: true)
- `REDIS_URL`: Redis connection URL (default: redis://localhost:6379/0)
- `REDIS_KEY_PREFIX`: Key prefix for namespacing (default: isvicre:)
- `REDIS_TTL_SECONDS`: Default TTL for cached values (default: 3600)

#### New Dependencies

- `redis>=7.1.0` - Redis client
- `hiredis>=3.3.0` - High-performance C parser for Redis

#### Testing

- 12 new Redis integration tests
- Total: 96 passing tests
- Tests work with or without Redis available

#### Stats

- Version: 0.9.0 → 1.0.0
- New files: 2 (redis_client.py, test_redis.py)
- Modified: 6 (cache.py, rate_limit.py, health.py, config.py, docker-compose.yml, pyproject.toml)

---

## [0.9.0] - 2025-11-25

### 🚀 Production Ready Infrastructure

#### Major Features

- **Health Check Endpoints**: `/health` and `/ready` for container orchestration
  - Liveness probe with comprehensive system checks
  - Readiness probe for traffic routing
  - Memory and temp directory health monitoring
- **Structured Logging (structlog)**: Production-ready async-aware logging
  - JSON format in production for log aggregators (ELK, Loki)
  - Pretty console output in development
  - Standardized log events
- **Prometheus Metrics**: Application metrics for monitoring
  - Request count and latency histograms
  - Tool usage metrics
  - Cache hit/miss counters
  - Rate limit event tracking
  - `/metrics` endpoint for Prometheus scraping

#### DevOps Infrastructure

- **Dockerfile**: Multi-stage build with security best practices
  - Non-root user (appuser)
  - uv for fast dependency installation
  - Health check built-in
  - Production-optimized settings
- **docker-compose.yml**: Complete stack definition
  - Application service with health checks
  - Prometheus metrics collection
  - Grafana dashboards (optional profile)
  - Named volumes for data persistence
- **prometheus.yml**: Pre-configured Prometheus scraping
  - Application metrics at 10s intervals
  - Useful PromQL query examples
- **GitHub Actions CI/CD**: Enhanced pipeline
  - Parallel lint, format, typecheck jobs
  - Test job with coverage
  - Docker build and test
  - Trivy security scanning

#### Developer Experience

- **Makefile**: 20+ commands for common tasks
  - `make dev` - Start development server
  - `make test` - Run tests
  - `make docker-up` - Start Docker stack
  - `make check` - Run all quality checks
- **.env.example**: Environment variable template
- **.dockerignore**: Optimized build context

#### New Dependencies

- `structlog>=25.5.0` - Structured logging
- `prometheus-client>=0.23.1` - Prometheus metrics

#### Stats

- New files: 8 (health.py, metrics.py, Dockerfile, docker-compose.yml, prometheus.yml, Makefile, .env.example, .dockerignore)
- CI jobs: 1 → 4 (lint, test, docker, security)
- Tests: 69 passing

---

## [0.8.0] - 2025-11-25

### 🔗 Tool Graph & Pipeline System

#### Major Features

- **Tool Graph Model**: Defined relationships between tools (`suggested_next`)
- **Pipeline Engine**: Secure inter-tool file transfer with TTL-based expiry
- **Pipeline Suggestions UI**: Dynamic "Sıradaki Adımlar" component
- **Flow Analytics**: Track tool-to-tool navigation patterns

#### New Tools (3)

1. **Image Metadata Inspector** (`image-metadata`)
   - EXIF metadata viewer and cleaner
   - GPS location privacy protection
   - Pipeline integration
2. **Image Cropper** (`image-cropper`)
   - Manual coordinate-based cropping
   - Pipeline-aware workflow
3. **PDF Splitter** (`pdf-splitter`)
   - Page range selection (e.g., "1-3,5,7-9")
   - Complements PDF Merger

#### Technical Improvements

- **Pipeline System**: `app/core/pipeline.py`
  - Cryptographically secure IDs (32-byte tokens)
  - 10-minute default TTL with auto-cleanup
  - In-memory metadata store
  - File isolation in temp directory
- **Tool Relationships**: All 13 tools have defined workflows
  - image-converter → image-resizer, image-metadata
  - image-resizer → image-metadata, image-cropper
  - pdf-merger → pdf-splitter
  - json-formatter → base64, url-encoder
- **Flow Analytics**: Track cross-tool navigation
  - `record_tool_flow(from_slug, to_slug)`
  - Top 10 flows in admin dashboard
  - Helps identify common workflows

#### Testing

- **11 New Tests**: Pipeline, flow analytics, new tools
- **Total**: 69 passing tests (was 58)
- **Coverage**: All new features tested

#### Stats

- Tools: 9 → 13 (+4 new, including QR Code Reader)
- Tests: 58 → 69 (+11)
- Lines of Code: ~2000 added
- Test Pass Rate: 100%

---

## [0.7.0] - 2025-11-24

### 🚀 Programmatic SEO & Content Engine

#### New Features

- **Rich SEO Metadata**: All 9 tools now have comprehensive Turkish content
  - Long descriptions (2-4 paragraphs per tool)
  - Use cases (3-5 realistic scenarios per tool)
  - FAQ sections (3-4 Q&A pairs per tool)
- **Dynamic SEO Meta Tags**: Tool-specific titles, descriptions, and keywords
- **JSON-LD Schema**: SoftwareApplication schema for all tool pages
- **Enhanced Sitemap**: Category-based priorities and lastmod dates
- **In-Memory Analytics**: Page view and search query tracking
- **Admin Analytics Dashboard**: View tool popularity and search trends

#### Performance & SEO

- Global SEO settings (SITE_NAME, SITE_TAGLINE, DEFAULT_SEO_DESCRIPTION)
- Automatic content sections on all tool pages
- Category-based sitemap priorities (IMAGE/OFFICE: 0.9, DEV: 0.8, SECURITY: 0.85)
- Structured data for better search engine visibility

#### Developer Experience

- New `tool_content.html` component for automatic content display
- Analytics API (`record_page_view`, `record_search_query`, `get_analytics_stats`)
- 13 new tests (analytics and SEO coverage)
- Comprehensive documentation updates

#### Documentation

- Updated README with SEO features
- Detailed v0.7.0 walkthrough
- Implementation plan and progress tracking

### 📊 Statistics

- **Total Tests**: 58 (all passing)
- **New Tests**: +13
- **Content Added**: ~6000 words of Turkish SEO content
- **Tools with Rich Content**: 9/9 (100%)

---

## [0.6.0] - 2025-11-23

### 🚀 Yeni Özellikler (New Features)

- **QR Kod Oluşturucu:** URL ve metinler için özelleştirilebilir QR kodlar oluşturma.
- **Şifre Oluşturucu:** Güvenli ve rastgele şifreler oluşturma (istemci tarafı kopyalama desteği ile).
- **Markdown Önizleme:** Markdown metinleri için canlı HTML önizleme editörü.
- **Admin Dashboard:** Araç kullanım istatistikleri, hata oranları, cache hit oranları ve rate limit olayları.

### ⚡ Performans ve Güvenlik (Performance & Security)

- **Rate Limiting:** Tüm araçlar için IP tabanlı hız sınırlaması (dakikalık istek ve saatlik upload limiti).
- **Caching:** Metin tabanlı araçlar (JSON, Base64, URL) için LRU cache entegrasyonu.
- **Observability:** Merkezi loglama ve metrik toplama sistemi.

### 🎨 Kullanıcı Arayüzü (UI/UX)

- **Bileşen Sistemi:** Tüm araçlar yeni `hero` ve `card` bileşenleri ile modernize edildi.
- **Tutarlı Tasarım:** Tüm sayfalarda ortak tasarım dili ve renk paleti.
- **Responsive:** Mobil uyumlu arayüz iyileştirmeleri.

## [0.5.0] - 2025-11-22

### Added

- **Configuration Management:**

  - Pydantic BaseSettings for environment-based configuration
  - Environment enum (DEV/STAGING/PROD)
  - Tool capability fields in Registry (`accepts_files`, `accepts_text`, `max_upload_mb`)

- **Security:**

  - Custom exception hierarchy (InvalidFileError, InvalidImageError, InvalidPDFError)
  - Enhanced PDF validation (checks for empty pages)
  - `cleanup_temp_files()` utility for safe file cleanup
  - IP-based rate limiting module (`app/core/rate_limit.py`)
  - Configurable request and upload limits

- **Observability:**

  - JSON-structured logging with `log_tool_call()`
  - Security event logging with `log_security_event()`
  - `track_tool_call()` context manager for automatic duration tracking
  - Comprehensive statistics API with per-tool metrics
  - Top tools tracking and error rate calculation

- **Performance:**

  - LRU cache module for text-based tools (`app/core/cache.py`)
  - MD5-based cache key generation
  - Deterministic result caching for JSON/Base64/URL tools

- **UI Components:**

  - Reusable Jinja2 components: hero, card, button, alert, tool_layout
  - Gradient-based hero sections
  - Dark-mode compatible components

- **Admin Dashboard:**
  - `/admin/stats` endpoint with ENV-based access control
  - Visual dashboard showing usage statistics
  - Per-tool metrics table (calls, successes, errors, avg duration)
  - Top 5 most-used tools display

### Changed

- Upgraded `app/core/config.py` from basic class to Pydantic BaseSettings
- Enhanced `app/core/upload.py` with better validation and error handling
- Refactored `app/core/observability.py` with improved stats structure
- Updated FastAPI initialization to use environment-aware settings
- All 6 tools now declare their capabilities via ToolInfo
- Admin endpoint now returns HTML template instead of raw JSON

### Fixed

- Import ordering lint errors in `app/main.py`
- Admin stats API test to match new response structure (HTML)

### Tests

- ✅ All 28 tests passing
- Updated test suite to match new observability API and admin HTML response

---

## [0.4.0] - 2025-11-21

### Added

- URL Tool with double-encoding protection
- Comprehensive test coverage for all developer tools
- Standardized hero headers and feature cards across all tools

### Fixed

- Critical double-encoding bug in URL Tool
- Restrictive safe characters for query string encoding

---

## [0.3.0] - 2025-11-20

### Added

- Base64 Converter tool
- JSON Formatter tool
- URL Encoder/Decoder tool

---

## [0.2.0] - 2025-11-19

### Added

- Image Converter with EXIF stripping
- Image Resizer with aspect ratio preservation
- PDF Merger with drag-and-drop interface

---

## [0.1.0] - 2025-11-18

### Added

- Initial project structure
- Tool Registry system
- Command Center (homepage)
- SEO infrastructure (sitemap, meta tags)
