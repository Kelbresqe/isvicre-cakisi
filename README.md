# İsviçre Çakısı (Swiss Army Knife) 🛠️

Modern, hızlı ve çok amaçlı web tabanlı araç seti. Geliştiriciler, tasarımcılar ve günlük kullanıcılar için pratik çözümler sunar.

![Version](https://img.shields.io/badge/version-1.2.0-blue)
![Python](https://img.shields.io/badge/python-3.13+-green)
![License](https://img.shields.io/badge/license-MIT-yellow)
![Tests](https://img.shields.io/badge/tests-96%20passing-success)

## 🚀 Özellikler

- **Modern Teknoloji Yığını:** Python 3.13+, FastAPI, HTMX, Alpine.js ve Tailwind CSS
- **Modüler Mimari:** "Registry Pattern" ile kolayca genişletilebilir yapı
- **Hızlı ve Güvenli:** `uv` paket yöneticisi, rate limiting ve `puremagic` ile dosya güvenliği
- **Production Ready:** Docker, Prometheus metrics, structured logging
- **Redis Entegrasyonu:** Dağıtık deployment için Redis desteği, otomatik fallback (v1.0.0)
- **🌙 Dark Mode:** Sistem tercihine duyarlı, localStorage ile kalıcı tema desteği (v1.2.0)
- **📱 PWA Desteği:** Masaüstüne kurulum, offline destek, uygulama kısayolları (v1.2.0)
- **⌨️ Klavye Kısayolları:** Hızlı navigasyon için kısayol tuşları (v1.2.0)
- **Kapsamlı Araçlar:** 18 araç tek bir yerde

## 🛠 Araçlar (Tools)

Bu depo yayınlanabilir durumdadır; kurulum, çalışma, test ve dağıtım notları aşağıda tek yerde toplanmıştır. Ayrıntılı sürüm geçmişi için `CHANGELOG.md`, katkı rehberi için `CONTRIBUTING.md` kullanın.

## ⚙️ Ortam Değişkenleri

Aşağıdaki değişkenler `.env` içinde tanımlanabilir:

| Değişken | Açıklama | Varsayılan |
| --- | --- | --- |
| `ENV` | Çalışma ortamı | `DEV` |
| `DEBUG` | Debug modu | `True` |
| `DOCS_ENABLED` | `/docs` ve `/redoc` açık mı | `True` |
| `REDIS_ENABLED` | Redis entegrasyonu | `true` |
| `REDIS_URL` | Redis bağlantı URL'i | `redis://localhost:6379/0` |
| `REDIS_KEY_PREFIX` | Redis anahtar öneki | `isvicre:` |
| `REDIS_TTL_SECONDS` | Cache TTL | `3600` |
| `MAX_UPLOAD_SIZE_MB` | Maksimum dosya yükleme boyutu | uygulama ayarı |

## 🚚 Dağıtım Notları

- Production dağıtımında `ENV=PROD`, `DEBUG=false`, `DOCS_ENABLED=false` ve `REDOC_ENABLED=false` kullanın.
- Redis opsiyoneldir; erişilemezse uygulama in-memory fallback ile çalışır.
- `health`, `ready` ve `metrics` uçları izleme için vardır; production ortamında erişim politikanızı reverse proxy veya network policy ile netleştirin.
- Docker stack’i için `make docker-up` kullanılabilir; monitoring stack’i için `make docker-mon` opsiyoneldir.

## 📦 Release Notes Özeti

- **1.2.0**: Dark mode, PWA desteği ve klavye kısayolları eklendi.
- **1.1.0**: Dice Roller, Hash Generator, Color Picker, Lorem Ipsum ve Base Converter eklendi.
- **1.0.0**: Redis entegrasyonu, dağıtık cache/rate limit ve health check iyileştirmeleri eklendi.
- **0.9.0**: Production Docker, metrics, structured logging ve CI/CD iyileştirildi.

## ⚠️ Bilinen Sınırlamalar

- Bazı operasyonel yüzeyler, deployment topolojisine bağlı olarak ek erişim kontrolü gerektirebilir.
- Çoklu worker kurulumlarında process içi bellek kullanan bileşenler tutarsız davranabilir.
- Dosya işleme akışlarında yayın öncesi güvenlik regresyon testleri çalıştırılmalıdır.


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

### Geliştirici Araçları (5)

| Araç                   | Açıklama                         |
| ---------------------- | -------------------------------- |
| **JSON Formatlayıcı**  | JSON doğrulama ve güzelleştirme  |
| **Base64 Dönüştürücü** | Metin/dosya Base64 encode/decode |
| **URL Kodlayıcı**      | URL encoding/decoding            |
| **Markdown Önizleme**  | Canlı Markdown editörü           |
| **Taban Dönüştürücü**  | Binary, Octal, Decimal, Hex      |

### Güvenlik Araçları (2)

| Araç                 | Açıklama                |
| -------------------- | ----------------------- |
| **Şifre Oluşturucu** | Güçlü rastgele şifreler |
| **Hash Üretici**     | MD5, SHA-256, File Hash |

### Tasarım Araçları (2)

| Araç            | Açıklama                      |
| --------------- | ----------------------------- |
| **Renk Seçici** | HEX, RGB, HSL, CMYK, Paletler |
| **Lorem Ipsum** | Rastgele metin üretici        |

### Oyun & Eğlence (1)

| Araç         | Açıklama                       |
| ------------ | ------------------------------ |
| **Zar Atma** | D4-D100, Özel notasyon (2d6+3) |

## 🏗 Mimari

Proje **Modular Monolith** yapısındadır:

```
app/
├── main.py              # FastAPI app entry point
├── core/                # Core modules
│   ├── config.py        # Pydantic Settings
│   ├── health.py        # Health check endpoints
│   ├── metrics.py       # Prometheus metrics
│   ├── observability.py # Structured logging (structlog)
│   ├── rate_limit.py    # IP-based rate limiting (Redis-backed)
│   ├── cache.py         # Hybrid cache (Redis + in-memory)
│   ├── redis_client.py  # Redis connection manager (v1.0.0)
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

Uygulama lokal geliştirmede `http://localhost:8000` veya `http://127.0.0.1:8000` adresinde çalışacaktır. Public erişim `https://caki.golgediyar.com` üzerinden cloudflared tüneli ile aynı OrbStack container'ına yönlenir.

Host-header doğrulaması dev ortamında `localhost`, `127.0.0.1`, IPv6 loopback (`::1` / `[::1]`) ve `caki.golgediyar.com` hostlarını kabul edecek şekilde yapılandırılmıştır. Eğer `Invalid host header` veya benzeri bir hata tekrar görünürse `.env` / compose içindeki `ENV`, `TRUSTED_HOSTS` ve `CORS_ORIGINS` ayarlarını kontrol edin, ardından `docker-compose up -d app` ile servisi yeniden oluşturun.

### Docker ile Çalıştırma

```bash
# Docker image oluşturun
make docker

# Container'ları başlatın (Redis dahil)
make docker-up

# Prometheus monitoring ile (opsiyonel)
make docker-mon
```

### Redis Konfigürasyonu (v1.0.0)

Redis opsiyoneldir. Redis olmadan uygulama in-memory fallback kullanır.

```bash
# Yerel Redis başlatma (opsiyonel)
docker run -d --name isvicre-redis -p 6379:6379 redis:7-alpine

# Environment variables
export REDIS_ENABLED=true
export REDIS_URL=redis://localhost:6379/0
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

## 📊 Monitoring

### Health Check Endpoints

| Endpoint       | Açıklama                                  |
| -------------- | ----------------------------------------- |
| `GET /health`  | Liveness probe - uygulama çalışıyor mu?   |
| `GET /ready`   | Readiness probe - trafik almaya hazır mı? |
| `GET /metrics` | Prometheus metrics                        |

### Health Response (v1.0.0)

```json
{
  "status": "healthy",
  "version": "1.0.0",
  "checks": {
    "temp_directory": { "status": "ok" },
    "memory": { "status": "ok" },
    "redis": { "status": "ok", "redis_version": "7.x.x" }
  }
}
```

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
