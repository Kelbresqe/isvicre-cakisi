# İsviçre Çakısı (Swiss Army Knife) 🛠️

Modern, hızlı ve çok amaçlı web tabanlı araç seti. Geliştiriciler, tasarımcılar ve günlük kullanıcılar için pratik çözümler sunar.

![Version](https://img.shields.io/badge/version-0.9.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Tests](https://img.shields.io/badge/tests-69%20passing-success)

## 🚀 Özellikler

- **Modern Teknoloji Yığını:** Python 3.13+, FastAPI, HTMX, Alpine.js ve Tailwind CSS
- **Modüler Mimari:** "Registry Pattern" ile kolayca genişletilebilir yapı
- **Hızlı ve Güvenli:** `uv` paket yöneticisi, rate limiting ve `puremagic` ile dosya güvenliği
- **Production Ready:** Docker, Prometheus metrics, structured logging (v0.9.0)
- **Kapsamlı Araçlar:** 13 araç tek bir yerde

## 🛠 Araçlar (Tools)

### Medya Araçları (8)

| Araç                     | Açıklama                                         |
| ------------------------ | ------------------------------------------------ |
| **Resim Dönüştürücü**    | PNG, JPEG, WEBP, GIF, TIFF, BMP, ICO formatları  |
| **Resim Boyutlandırıcı** | Resimleri yeniden boyutlandırma ve optimize etme |
| **Resim Kırpıcı**        | Görselleri istenilen koordinatlarda kırpma       |
| **Resim Metadata**       | EXIF bilgilerini görüntüleme ve temizleme        |
| **PDF Birleştirici**     | Birden fazla PDF'i tek dosyada birleştirme       |
| **PDF Ayırıcı**          | PDF dosyalarını sayfalara ayırma                 |
| **QR Kod Oluşturucu**    | Özelleştirilebilir QR kodlar                     |
| **QR Kod Okuyucu**       | Resimden QR kod içeriğini okuma                  |

### Geliştirici Araçları (4)

| Araç                   | Açıklama                         |
| ---------------------- | -------------------------------- |
| **JSON Formatlayıcı**  | JSON doğrulama ve güzelleştirme  |
| **Base64 Dönüştürücü** | Metin/dosya Base64 encode/decode |
| **URL Kodlayıcı**      | URL encoding/decoding            |
| **Markdown Önizleme**  | Canlı Markdown editörü           |

### Güvenlik Araçları (1)

| Araç                 | Açıklama                |
| -------------------- | ----------------------- |
| **Şifre Oluşturucu** | Güçlü rastgele şifreler |

## 🏗 Mimari

Proje **Modular Monolith** yapısındadır:

```
app/
├── main.py              # FastAPI app entry point
├── core/                # Core modules
│   ├── config.py        # Pydantic Settings
│   ├── health.py        # Health check endpoints (v0.9.0)
│   ├── metrics.py       # Prometheus metrics (v0.9.0)
│   ├── observability.py # Structured logging (structlog)
│   ├── rate_limit.py    # IP-based rate limiting
│   ├── cache.py         # LRU cache
│   └── pipeline.py      # Inter-tool file transfer
├── tools/               # Tool modules
│   ├── registry.py      # Tool registry pattern
│   └── <tool_slug>/     # Each tool in isolated folder
└── templates/           # Jinja2 templates
```

## 💻 Kurulum

### Gereksinimler

- Python 3.13+
- [uv](https://github.com/astral-sh/uv) (Modern Python paket yöneticisi)

### Yerel Geliştirme

```bash
# Projeyi klonlayın
git clone https://github.com/Kelbresqe/isvicre-cakisi.git
cd isvicre-cakisi

# Bağımlılıkları yükleyin
make install
# veya: uv sync

# Environment dosyasını oluşturun
cp .env.example .env

# Uygulamayı başlatın
make dev
# veya: uv run uvicorn app.main:app --reload
```

Uygulama `http://localhost:8000` adresinde çalışacaktır.

### Docker ile Çalıştırma (v0.9.0)

```bash
# Docker image oluşturun
make docker

# Container'ları başlatın
make docker-up

# Prometheus monitoring ile (opsiyonel)
make docker-mon
```

## 🧪 Testler

```bash
# Tüm testleri çalıştır
make test

# Coverage ile
make test-cov

# Lint & format kontrolü
make check
```

## 📊 Monitoring (v0.9.0)

### Health Check Endpoints

| Endpoint       | Açıklama                                  |
| -------------- | ----------------------------------------- |
| `GET /health`  | Liveness probe - uygulama çalışıyor mu?   |
| `GET /ready`   | Readiness probe - trafik almaya hazır mı? |
| `GET /metrics` | Prometheus metrics                        |

### Prometheus Metrics

- `isvicre_cakisi_requests_total` - HTTP request sayısı
- `isvicre_cakisi_tool_calls_total` - Tool API çağrı sayısı
- `isvicre_cakisi_request_latency_seconds` - İstek gecikme histogramı
- `isvicre_cakisi_cache_hits_total` - Cache hit sayısı

## 🔧 Makefile Komutları

```bash
make help        # Tüm komutları listele
make dev         # Development server
make test        # Testleri çalıştır
make lint        # Linter (ruff)
make format      # Code formatter (black)
make docker-up   # Docker başlat
make docker-logs # Container logları
```

## 📝 Lisans

Bu proje MIT lisansı ile lisanslanmıştır.
