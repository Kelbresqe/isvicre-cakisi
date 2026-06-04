# Güvenlik Düzeltmeleri — Öncelikli Uygulama Planı

Proje: isvicre-cakisi (İsviçre Çakısı, FastAPI)
Kapsam: Yalnızca güvenlik düzeltmeleri. Genel refactor, dokümantasyon veya güvenlik dışı iyileştirme kapsam dışıdır.
Kaynak: code-reviewer + qa-tester + acceptance-judge bulguları, kod tabanına karşı doğrulandı.

## Doğrulama Notu (kod kanıtı)
- app/tools/pdf_merger/router.py:193  TEMP_DIR / filename, containment yok (path traversal/LFI okuma)
- app/core/config.py:32,120-122  ENV=DEV, DEBUG=True, DOCS/REDOC enabled varsayılan
- app/tools/pdf_splitter/router.py:119  split_in_{file.filename} (write traversal)
- app/tools/image_cropper/router.py:112  crop_in_{file.filename} (write traversal)
- app/main.py  CORS/TrustedHost middleware mount EDILMEMIS (config.py:92-99 ölü)
- app/main.py:214,124  /metrics ve /ready auth yok
- tests/  güvenlik regresyon testi YOK

## P1 — CRITICAL (production öncesi zorunlu)

### P1.1 Path traversal / LFI — indirme yolu çözümleyici
Alan: app/tools/pdf_merger/router.py:193 (/download/{filename})
Risk: filename = ../../etc/passwd ile TEMP_DIR dışındaki dosyalar okunup FileResponse ile sızdırılır. Kimlik doğrulamasız LFI (Critical).
Önerilen düzeltme:
  - Ortak güvenli çözümleyici ekle (örn. app/core/safe_path.py): candidate = (TEMP_DIR / filename).resolve(); base = TEMP_DIR.resolve(); candidate.is_relative_to(base) değilse 404.
  - Ek olarak os.path.basename(filename) ile path bileşenlerini düşür; mutlak/UNC ve symlink kaçışlarını reddet.
  - Tüm /download* uçları bu çözümleyiciyi kullansın.
Bağımlılıklar: yok (Python 3.9+ is_relative_to). P3 yardımcı modülünü P1.1 ile aynı PR icinde oluştur.
Doğrulama: tests/test_security_path_traversal.py — ../, %2e%2e, mutlak yol, symlink vakaları 404/400 döndürür; meşru dosya 200.
Kabul Kriteri (AC-1): TEMP_DIR dışına çözümlenen hiçbir istek dosya döndürmez; tüm traversal payloadları reddedilir ve testle kanıtlanır.

### P1.2 Public sunucu DEV/DEBUG modunda
Alan: app/core/config.py:32 (ENV=DEV), :120 (DEBUG=True), :121-122 (DOCS/REDOC enabled)
Risk: Canlı sunucu debug traceback (stack/secret sızıntısı), açık /docs ve /redoc, admin/stats dev kontrolü ile production exposure (Critical).
Önerilen düzeltme:
  - Güvenli varsayilanlar: ENV=PROD, DEBUG=False, DOCS_ENABLED=False, REDOC_ENABLED=False. Dev için açıkça .env ile override.
  - VEYA: varsayilani DEV birakip deployment .env zorunlulugunu CI/startup assert ile dayat (is_prod iken DEBUG/DOCS False olmali, degilse startup hata).
  - docs_url/redoc_url zaten is_prod iken None donuyor; ENV=PROD ayarlanmazsa bu koruma devreye girmez — kök sorun varsayilan ENV.
Bağımlılıklar: deployment .env / ortam değişkeni yönetimi (devops-integrator).
Doğrulama: tests/test_security_config.py — PROD profilinde DEBUG False, docs_url/redoc_url None; startup assert testi.
Kabul Kriteri (AC-2): Production ortamında DEBUG=False, /docs ve /redoc 404; yanlış konfig startup'ta hata verir.

## P2 — HIGH (production öncesi zorunlu)

### P2.1 Write-path traversal — yüklenen dosya adı
Alan: app/tools/pdf_splitter/router.py:119, app/tools/image_cropper/router.py:112
Risk: file.filename kullanıcı kontrollü; split_in_../../x ile TEMP_DIR dışına yazma → dosya üzerine yazma / yol manipülasyonu (High).
Önerilen düzeltme:
  - Girdi temp adlarında file.filename KULLANMA; uuid4 üret: split_in_{uuid4().hex}.pdf, crop_in_{uuid4().hex}.{ext}.
  - Uzantıyı kullanıcı adından değil doğrulanmış content_type/MIME whitelist'ten türet (config.py ALLOWED_*_MIME_TYPES).
  - Tüm araç router'larında yazma yollarını tara; aynı kalıbı uygula.
Bağımlılıklar: yok. P1.1 safe_path yardımcısı ile tutarlı.
Doğrulama: tests/test_security_upload_filename.py — filename=../evil ile yazılan yol daima TEMP_DIR içinde ve uuid tabanlı.
Kabul Kriteri (AC-3): Yüklenen hiçbir dosya kullanıcı sağladığı adla diske yazılmaz; tüm yazma yolları uuid4 tabanlı ve TEMP_DIR içindedir.

### P2.2 CORS / TrustedHost middleware mount edilmemiş
Alan: app/main.py (mount yok); config.py:92-99 (TRUSTED_HOSTS, CORS_ORIGINS tanımlı ama ölü)
Risk: Host header injection, beklenmeyen origin'lerden tarayıcı çağrıları; tanımlı güvenlik konfigi etkisiz (High).
Önerilen düzeltme:
  - app/main.py'e TrustedHostMiddleware(allowed_hosts=settings.TRUSTED_HOSTS) ve CORSMiddleware(allow_origins=settings.CORS_ORIGINS, allow_credentials, methods/headers daraltılmış) ekle.
  - TRUSTED_HOSTS varsayılanındaki *.vercel.app gibi geniş kalıpları production için sıkılaştır; CORS_ORIGINS'i prod domainine indir.
Bağımlılıklar: starlette.middleware (FastAPI ile gelir). Prod host/origin listesi (devops-integrator).
Doğrulama: tests/test_security_middleware.py — sahte Host header reddedilir; izinsiz Origin'e CORS başlığı verilmez; izinli Origin geçer.
Kabul Kriteri (AC-4): TrustedHost ve CORS middleware fiilen mount edilmiştir ve config değerlerinden beslenir; izin dışı host/origin reddedilir.

### P2.3 /metrics ve /ready auth yok
Alan: app/main.py:214 (/metrics), :124 (/ready)
Risk: Prometheus metrikleri ve readiness ayrıntıları kimlik doğrulamasız ifşa → iç durum/bilgi sızıntısı, recon (High).
Önerilen düzeltme:
  - /metrics'i internal network/scrape kimliğine kısıtla: paylaşılan token başlığı veya IP allowlist dependency, ya da reverse proxy seviyesinde koru.
  - /ready yanıtını minimuma indir (reason ayrıntısını prod'ta kıs); /health zaten liveness için yeterli.
Bağımlılıklar: deploy topolojisi (reverse proxy / network policy) — devops-integrator ile koordine.
Doğrulama: tests/test_security_endpoints.py — tokensız /metrics 401/403; izinli erişim 200.
Kabul Kriteri (AC-5): /metrics yetkisiz erişime kapalıdır (token/IP/proxy) ve /ready hassas iç ayrıntı sızdırmaz; testle kanıtlanır.

## P3 — Güvenlik Regresyon Testleri (CI gate, zorunlu)

### P3.1 Otomatik güvenlik regresyon test paketi
Alan: tests/ (mevcut test_* dosyası YOK)
Risk: P1/P2 düzeltmeleri doğrulanamaz ve gelecekte sessizce geri gelebilir; QA kalite kapısı bu nedenle FAIL.
Önerilen düzeltme:
  - pytest + httpx/TestClient ile yukarıdaki AC-1..AC-5 testlerini ekle.
  - CI pipeline'ına zorunlu adım: güvenlik testleri geçmeden merge/deploy yok.
Bağımlılıklar: P1.1, P1.2, P2.1, P2.2, P2.3 düzeltmeleri (testler bunları doğrular). CI yapısı devops-integrator.
Doğrulama: CI çalıştırmasında tüm güvenlik testleri yeşil; kasıtlı regresyon (örn. middleware kaldırma) testi kırar.
Kabul Kriteri (AC-6): AC-1..AC-5 için otomatik testler CI'da zorunlu kapı olarak çalışır ve düzeltmelerin geri gelmesini engeller.

## Uygulama Sırası ve Bağımlılık Özeti
1. P3 yardımcıları + P1.1 (safe_path + download resolver)
2. P1.2 (prod config defaults / startup assert)
3. P2.1 (uuid4 yazma adları)
4. P2.2 (TrustedHost + CORS mount)
5. P2.3 (/metrics + /ready koruması)
6. P3.1 (CI güvenlik test kapısı — tümünü doğrular)

Kapsam dışı (bu kartta önerilmez): rate_limit.py _get_client_ip duplikasyonu, multi-worker in-memory state — güvenlik dışı/medium, ayrı kartta ele alınmalı.
