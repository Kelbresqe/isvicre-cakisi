# İsviçre Çakısı — Uygulanabilir Düzeltme Checklist'i

Kaynak raporlar:
- `QUALITY_ASSESSMENT_REPORT.md`
- `SECURITY_REMEDIATION_PLAN.md`

Amaç: İki rapordaki tüm bulguları güvenlik, kalite, test, build/deploy ve dokümantasyon başlıklarında; öncelik, etki, ilgili dosya/modül, önerilen çözüm ve doğrulama yöntemiyle izlenebilir tek plana dönüştürmek.

Öncelik tanımı:
- **P1 / Kritik:** Production öncesi zorunlu, açık güvenlik veya canlı ortam riski.
- **P2 / Yüksek:** Production öncesi zorunlu veya güvenlik/operasyon etkisi yüksek.
- **P3 / Orta:** Production sonrası kısa vadeli kalite, dayanıklılık veya bakım işi.
- **P4 / Düşük:** UX, temizlik veya süreç iyileştirmesi.

## 1. Güvenlik

### [ ] SEC-01 — Path traversal / LFI indirme açığını kapat
- **Öncelik:** P1 / Kritik
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P1.1, AC-1; `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 2, Quick Wins 2, Kanban Kartı 2.
- **Etki:** `filename=../../...` gibi payload'lar `TEMP_DIR` dışındaki dosyaları `FileResponse` ile sızdırabilir.
- **İlgili dosya/modül:** `app/tools/pdf_merger/router.py` `/download/{filename}`; tüm diğer `/download*` uçları; yeni ortak yardımcı için `app/core/safe_path.py`.
- **Aksiyon:** Ortak güvenli path resolver ekle. `base = TEMP_DIR.resolve()`, `candidate = (base / basename).resolve()` yaklaşımıyla mutlak yol, `..`, URL-encoded traversal ve symlink kaçışlarını reddet. `candidate.is_relative_to(base)` kontrolü başarısızsa `404` veya `400` dön. Tüm download endpoint'leri bu resolver'ı kullansın.
- **Doğrulama:** `tests/test_security_path_traversal.py` ekle. `../`, `%2e%2e`, mutlak yol ve symlink vakaları reddedilmeli; geçerli temp dosyası `200` dönmeli.
- **Kabul kriteri:** `TEMP_DIR` dışına çözümlenen hiçbir istek dosya döndürmez.

### [ ] SEC-02 — Production ortamını güvenli varsayılanlara al
- **Öncelik:** P1 / Kritik
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P1.2, AC-2; `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 1, Quick Wins 1, Kanban Kartı 1.
- **Etki:** Public servis dev/debug modda çalışırsa traceback, `/docs`, `/redoc`, admin/stats ve iç bilgi yüzeyleri açılır.
- **İlgili dosya/modül:** `app/core/config.py`, `app/main.py`, deployment `.env` / compose ortam değişkenleri.
- **Aksiyon:** Varsayılanları production-safe yap: `ENV=PROD`, `DEBUG=False`, `DOCS_ENABLED=False`, `REDOC_ENABLED=False`. Dev modu yalnızca açık `.env` override ile açılmalı. Production'da `DEBUG` veya docs açık kalırsa startup assertion ile uygulama başlamamalı.
- **Doğrulama:** `tests/test_security_config.py` ekle. PROD profilinde debug kapalı, docs/redoc URL'leri `None`, `/docs` ve `/redoc` `404` olmalı. Yanlış prod konfigürasyonu startup'ta hata vermeli.
- **Kabul kriteri:** Public production ortamında debug ve dokümantasyon yüzeyleri kapalıdır.

### [ ] SEC-03 — Upload/write path traversal riskini kaldır
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P2.1, AC-3; `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 2, Quick Wins 3.
- **Etki:** Kullanıcı kontrollü `file.filename`, temp dosya adına girerse `TEMP_DIR` dışına yazma veya yol manipülasyonu doğurabilir.
- **İlgili dosya/modül:** `app/tools/pdf_splitter/router.py`, `app/tools/image_cropper/router.py`, benzer upload/write router'ları.
- **Aksiyon:** Diskte yazılan temp adlarında `file.filename` kullanma. `uuid4().hex` tabanlı ad üret: `split_in_{uuid}.pdf`, `crop_in_{uuid}.{ext}`. Uzantıyı kullanıcı adından değil doğrulanmış MIME/content-type whitelist'inden türet. Tüm upload router'larını aynı kalıp için tara.
- **Doğrulama:** `tests/test_security_upload_filename.py` ekle. `filename=../evil` ile yükleme denendiğinde yazılan dosya adı UUID tabanlı ve `TEMP_DIR` içinde kalmalı.
- **Kabul kriteri:** Yüklenen hiçbir dosya kullanıcı sağladığı adla diske yazılmaz.

### [ ] SEC-04 — CORS ve TrustedHost middleware'lerini gerçekten mount et
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P2.2, AC-4; `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 3, Quick Wins 4, Kanban Kartı 3.
- **Etki:** Tanımlı güvenlik konfigürasyonu uygulanmadığı için Host header ve Origin kontrolleri etkisiz kalır.
- **İlgili dosya/modül:** `app/main.py`, `app/core/config.py` `TRUSTED_HOSTS`, `CORS_ORIGINS`.
- **Aksiyon:** `TrustedHostMiddleware(allowed_hosts=settings.TRUSTED_HOSTS)` ve `CORSMiddleware(allow_origins=settings.CORS_ORIGINS, ...)` ekle. Production host/origin listesini gerçek domainlerle sınırla; geniş wildcard'ları prod için kaldır.
- **Doğrulama:** `tests/test_security_middleware.py` ekle. Sahte `Host` reddedilmeli; izinsiz `Origin` için CORS başlığı verilmemeli; izinli origin geçmeli.
- **Kabul kriteri:** Middleware'ler uygulamada mount edilmiştir ve config değerlerinden beslenir.

### [ ] SEC-05 — `/metrics` ve `/ready` erişim politikasını sıkılaştır
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P2.3, AC-5; `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 5.
- **Etki:** Metrikler ve readiness ayrıntıları kimlik doğrulamasız recon ve iç durum sızıntısı sağlar.
- **İlgili dosya/modül:** `app/main.py` `/metrics`, `/ready`; reverse proxy / network policy.
- **Aksiyon:** `/metrics` için token header, IP allowlist veya reverse-proxy koruması uygula. `/ready` yanıtını prod'da minimuma indir; ayrıntılı hata/reason bilgilerini yalnızca dev/internal ortamda göster.
- **Doğrulama:** `tests/test_security_endpoints.py` ekle. Tokensız `/metrics` `401/403`, yetkili erişim `200` dönmeli. Prod `/ready` hassas ayrıntı sızdırmamalı.
- **Kabul kriteri:** Operasyon endpoint'leri yetkisiz erişime ve bilgi ifşasına kapalıdır.

### [ ] SEC-06 — Public admin/docs/metrics yüzeylerini tek env politikasıyla yönet
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 1 ve 5; `SECURITY_REMEDIATION_PLAN.md` P1.2, P2.3.
- **Etki:** Farklı kontroller dağınık kalırsa prod'da bir yüzey açık unutulabilir.
- **İlgili dosya/modül:** `app/core/config.py`, `app/main.py`, deployment env.
- **Aksiyon:** `settings.is_prod` altında docs, redoc, debug, detailed readiness ve metrics auth davranışlarını merkezi hale getir. Prod güvenlik ihlallerini startup'ta fail-fast yap.
- **Doğrulama:** Config testleri ve endpoint testleri aynı prod profilinde koşmalı.
- **Kabul kriteri:** Prod/dev ayrımı tek ve testlenmiş politika üzerinden yürür.

## 2. Kalite ve Mimari

### [ ] QUAL-01 — `rate_limit.py` içindeki duplike `_get_client_ip` kodunu temizle
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kategori Bazlı Bulgu Tablosu, Quick Wins 5; `SECURITY_REMEDIATION_PLAN.md` kapsam dışı notu.
- **Etki:** Duplike client IP çözümü bakım hatası ve proxy arkasında tutarsız rate-limit davranışı doğurabilir.
- **İlgili dosya/modül:** `app/core/rate_limit.py`.
- **Aksiyon:** Tek `_get_client_ip` implementasyonu bırak. Proxy header güvenini yalnızca trusted proxy yapılandırmasıyla kullan. Testlerin beklediği davranışı koru.
- **Doğrulama:** Mevcut `tests/test_rate_limit.py` ve eklenecek proxy IP testleri geçmeli.
- **Kabul kriteri:** Client IP çözümü tek yerde, deterministik ve testlidir.

### [ ] QUAL-02 — Pipeline ve sayaç state'ini çoklu worker uyumlu yap
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 4, Orta Vade, Kanban Kartı 4.
- **Etki:** Birden fazla worker çalıştığında in-memory pipeline/store bölünür; kullanıcı akışları ve analitik tutarsızlaşır.
- **İlgili dosya/modül:** `app/core/pipeline.py`, analytics/metrics sayaçları, Redis entegrasyonu, Docker worker ayarı.
- **Aksiyon:** Pipeline ve gerekli sayaç state'ini Redis'e taşı veya deployment'da tek-worker garantisini açıkça enforce et. Redis bağlantısı yoksa davranışı net fallback ve uyarıyla sınırla.
- **Doğrulama:** Çoklu worker simülasyonu veya entegrasyon testiyle farklı process'lerde state tutarlılığı doğrulanmalı. Redis kapalı fallback senaryosu testlenmeli.
- **Kabul kriteri:** Production deployment'da state kaybı veya worker'a göre farklı sonuç oluşmaz.

### [ ] QUAL-03 — `mypy` ve linter kurallarını kademeli sıkılaştır
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kategori Bazlı Bulgu Tablosu, Quick Wins 6, Orta Vade, Kanban Kartı 5.
- **Etki:** Gevşek tip kontrolü regresyonları ve `Any` kaynaklı runtime hatalarını gizler.
- **İlgili dosya/modül:** `pyproject.toml`, `app/**`, `tests/**`.
- **Aksiyon:** Önce yeni kod için stricter mypy kuralları ekle; bariz `Any` ve eksik annotation sorunlarını düzelt. Sonra modül modül strict kapsamını genişlet.
- **Doğrulama:** `uv run mypy app tests` ve `uv run ruff check .` CI gate olarak geçmeli.
- **Kabul kriteri:** Yeni kritik modüller typed, lint temiz ve CI tarafından korunur.

### [ ] QUAL-04 — UX hata akışlarını güvenlik düzeltmeleriyle uyumlu hale getir
- **Öncelik:** P4 / Düşük-Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` UX satırı, Daha Sonra, UX notları.
- **Etki:** Güvenlik nedeniyle reddedilen dosya/istek akışları kullanıcıya belirsiz hata gösterebilir.
- **İlgili dosya/modül:** İlgili tool router'ları, templates, frontend/HTMX hata gösterimleri.
- **Aksiyon:** Traversal, MIME, boyut, yetkisiz metrics gibi reddedilen durumlar için kullanıcıya güvenli ve açıklayıcı hata mesajları göster. Hassas path veya iç exception bilgisi göstermeme kuralını koru.
- **Doğrulama:** Manuel UX smoke testi ve HTML rendering testleri.
- **Kabul kriteri:** Kullanıcı güvenlik reddinin sebebini anlar; sistem iç bilgisi sızmaz.

## 3. Test ve CI

### [ ] TEST-01 — Güvenlik regresyon test paketini ekle
- **Öncelik:** P2 / Yüksek, SEC-01..SEC-05 için zorunlu gate
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` P3.1, AC-6; `QUALITY_ASSESSMENT_REPORT.md` Entegrasyon Testleri, Orta Vade, Kanban Kartı 5.
- **Etki:** Kritik güvenlik açıkları düzelse bile test yoksa regresyon sessizce geri dönebilir.
- **İlgili dosya/modül:** `tests/test_security_path_traversal.py`, `tests/test_security_upload_filename.py`, `tests/test_security_config.py`, `tests/test_security_middleware.py`, `tests/test_security_endpoints.py`, CI workflow.
- **Aksiyon:** AC-1..AC-5'i otomatik pytest testlerine dönüştür. TestClient/httpx ile endpoint seviyesinde doğrula. Gerekirse temp dizin fixture'ları ve env monkeypatch kullan.
- **Doğrulama:** `uv run pytest -q` tüm testlerde yeşil; kasıtlı regresyonlar ilgili testi kırar.
- **Kabul kriteri:** Güvenlik testleri CI'da zorunlu merge/deploy kapısıdır.

### [ ] TEST-02 — Deploy/runtime davranışı için smoke ve readiness testlerini genişlet
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` DevOps/Dağıtım, Entegrasyon Testleri, Kısa/Orta Vade.
- **Etki:** Production env, middleware ve worker ayarları yalnızca unit testle doğrulanmazsa deploy sonrası kırılabilir.
- **İlgili dosya/modül:** Docker/compose dosyaları, `app/main.py`, health/ready endpoints, CI deploy smoke adımı.
- **Aksiyon:** Prod profiliyle container ayağa kaldıran smoke check ekle. `/health` public liveness için çalışmalı; `/ready` minimal ve güvenli dönmeli; `/docs` kapalı olmalı; middleware host/origin davranışı doğrulanmalı.
- **Doğrulama:** CI veya release pipeline'da container smoke komutu.
- **Kabul kriteri:** Prod imajı güvenli ayarlarla ayağa kalkar ve temel endpoint'ler beklenen güvenlik davranışını verir.

### [ ] TEST-03 — Rate limit ve proxy IP testlerini sağlamlaştır
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Orta Vade; QUAL-01.
- **Etki:** Proxy arkasında yanlış client IP kullanımı rate-limit bypass veya yanlış kullanıcı bloklama doğurabilir.
- **İlgili dosya/modül:** `app/core/rate_limit.py`, `tests/test_rate_limit.py`.
- **Aksiyon:** Trusted/untrusted proxy header senaryolarını testle. Duplicate kod temizliği sonrası davranışı sabitle.
- **Doğrulama:** `uv run pytest tests/test_rate_limit.py -q`.
- **Kabul kriteri:** Proxy IP çözümü testlenmiş policy'ye uygun çalışır.

## 4. Build / Deploy / Operasyon

### [ ] DEPLOY-01 — Production env ve deployment konfigürasyonunu güvenli hale getir
- **Öncelik:** P1 / Kritik
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 1, Kısa Vade; `SECURITY_REMEDIATION_PLAN.md` P1.2.
- **Etki:** Kod güvenli olsa bile yanlış env public yüzeyi tekrar dev moda alabilir.
- **İlgili dosya/modül:** `.env`, compose/orbstack/cloudflared yapılandırması, deployment secrets, startup command.
- **Aksiyon:** Public servis için `ENV=PROD`, `DEBUG=false`, docs/redoc disabled, production host/origin listesi ve metrics auth secret'ını ayarla. Dev `.env.example` ile prod secret/env örneğini ayır.
- **Doğrulama:** Public veya staging smoke: `/docs` 404, `/redoc` 404, debug traceback yok, `/metrics` korumalı.
- **Kabul kriteri:** Canlı deployment güvenli prod profiliyle çalışır.

### [ ] DEPLOY-02 — Çoklu worker stratejisini netleştir
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Kritik Risk 4, DevOps satırı, Orta Vade.
- **Etki:** In-memory state çoklu worker ile veri bölünmesi ve kullanıcı işlem kaybı doğurur.
- **İlgili dosya/modül:** Dockerfile/compose/gunicorn/uvicorn worker ayarı, Redis config, `app/core/pipeline.py`.
- **Aksiyon:** Redis migration tamamlanana kadar tek-worker enforce et veya Redis-backed state'i zorunlu yap. Worker sayısı ve state backend kararını deployment dokümanına yaz.
- **Doğrulama:** Runtime config çıktısında worker/state backend görünür olmalı; smoke test tutarlılığı doğrulamalı.
- **Kabul kriteri:** Worker sayısı ile state backend arasında çelişki yoktur.

### [ ] DEPLOY-03 — Release / rollback / backup otomasyonu ekle
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` DevOps/Dağıtım satırı, Daha Sonra, Kanban Kartı 6.
- **Etki:** Hatalı release sonrası geri dönüş ve veri koruma süreci manuel kalır.
- **İlgili dosya/modül:** CI/CD workflow, deployment scripts, backup storage, runbook.
- **Aksiyon:** Versiyonlu imaj/tag, health-gated deploy, rollback komutu ve backup planı oluştur. Release öncesi test/security gate zorunlu olsun.
- **Doğrulama:** Staging üzerinde rollback tatbikatı; backup restore denemesi.
- **Kabul kriteri:** Deploy, rollback ve backup adımları otomatik veya runbook ile tekrarlanabilir.

### [ ] DEPLOY-04 — Observability ve alarm kurallarını üretim için tamamla
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` Daha Sonra, DevOps/Dağıtım, Observability notları.
- **Etki:** Güvenlik/availability sorunları üretimde geç fark edilir.
- **İlgili dosya/modül:** metrics exporter, logging/structlog config, alerting stack, `/metrics` koruması.
- **Aksiyon:** Error rate, latency, health/readiness, disk/temp usage ve security rejection metrikleri için alarm tanımla. `/metrics` korumasını bozmadan scrape yapılandır.
- **Doğrulama:** Alert dry-run veya staging alarm testi.
- **Kabul kriteri:** Kritik hata ve kapasite sorunları için izlenebilir alarm vardır.

## 5. Dokümantasyon

### [ ] DOC-01 — Production güvenlik konfigürasyonu dokümante et
- **Öncelik:** P2 / Yüksek
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` README/Dokümantasyon, Kısa Vade, Kanban Kartı 1 ve 3; `SECURITY_REMEDIATION_PLAN.md` P1.2, P2.2, P2.3.
- **Etki:** Operatörler doğru env, host/origin ve metrics auth ayarlarını bilmezse güvenli kod yanlış çalıştırılabilir.
- **İlgili dosya/modül:** `README.md`, `.env.example`, ops/runbook dokümanı.
- **Aksiyon:** `ENV`, `DEBUG`, docs/redoc, `TRUSTED_HOSTS`, `CORS_ORIGINS`, metrics token/IP policy ve public domain ayarlarını açıklayan production checklist ekle.
- **Doğrulama:** Yeni bir operatör dokümana göre staging'i prod profiliyle ayağa kaldırabilmeli.
- **Kabul kriteri:** Güvenli production çalıştırma adımları eksiksiz ve günceldir.

### [ ] DOC-02 — Release / rollback / backup runbook'u yaz
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `QUALITY_ASSESSMENT_REPORT.md` DevOps release/rollback/backup bulgusu, Kanban Kartı 6.
- **Etki:** Incident sırasında geri dönüş süresi uzar ve veri kaybı riski artar.
- **İlgili dosya/modül:** `README.md` veya `docs/OPERATIONS.md`, deploy scripts.
- **Aksiyon:** Deploy öncesi kontroller, smoke test komutları, rollback adımları, backup/restore prosedürü ve sorumlulukları yaz.
- **Doğrulama:** Runbook dry-run ile uygulanmalı.
- **Kabul kriteri:** Operasyon adımları tek dokümandan uygulanabilir.

### [ ] DOC-03 — Güvenlik test ve kabul kriterlerini dokümante et
- **Öncelik:** P3 / Orta
- **Kaynak izleme:** `SECURITY_REMEDIATION_PLAN.md` AC-1..AC-6; `QUALITY_ASSESSMENT_REPORT.md` Prod kalite kapıları.
- **Etki:** Gelecek değişikliklerde hangi güvenlik davranışlarının korunacağı belirsizleşir.
- **İlgili dosya/modül:** `README.md`, `tests/`, CI docs.
- **Aksiyon:** AC-1..AC-6 listesini geliştirici dokümanına ekle. Güvenlik testlerinin nasıl çalıştırılacağını ve CI'da neyi gate ettiğini yaz.
- **Doğrulama:** `uv run pytest -q` ve security-specific test komutları dokümandan çalıştırılabilmeli.
- **Kabul kriteri:** Her kritik/yüksek güvenlik aksiyonu test ve dokümanda izlenebilir.

## 6. Önerilen uygulama sırası

1. **SEC-01 + TEST-01 ilgili path traversal testleri** — LFI riskini kapatır.
2. **SEC-02 + DEPLOY-01 + config testleri** — public dev/debug riskini kapatır.
3. **SEC-03 + upload filename testleri** — write traversal riskini kapatır.
4. **SEC-04 + middleware testleri** — Host/CORS politikalarını etkinleştirir.
5. **SEC-05 + endpoint auth testleri** — metrics/ready bilgi ifşasını azaltır.
6. **TEST-01 tamamı CI gate** — AC-1..AC-6 regresyon korumasını sağlar.
7. **QUAL-02 + DEPLOY-02** — çoklu worker/state tutarsızlığını giderir.
8. **QUAL-01 + TEST-03** — rate-limit ve proxy IP davranışını temizler.
9. **QUAL-03** — tip/lint kalite kapısını güçlendirir.
10. **DEPLOY-03 + DEPLOY-04 + DOC-01..DOC-03** — operasyon ve dokümantasyon kapanışını yapar.
11. **QUAL-04** — güvenlik sonrası UX hata akışlarını toparlar.

## 7. Production'a çıkış için minimum kabul kapısı

Production onayı için aşağıdakiler tamamlanmadan release yapılmamalı:

- [ ] SEC-01, SEC-02, SEC-03, SEC-04, SEC-05 tamamlandı.
- [ ] DEPLOY-01 tamamlandı ve staging/public smoke ile doğrulandı.
- [ ] TEST-01 kapsamındaki AC-1..AC-6 testleri CI'da zorunlu gate oldu.
- [ ] `uv run pytest -q` yeşil.
- [ ] `/docs` ve `/redoc` production'da kapalı.
- [ ] `/metrics` yetkisiz erişime kapalı.
- [ ] `TEMP_DIR` dışına okuma/yazma traversal testleri başarısız saldırı olarak doğrulandı.
- [ ] Çoklu worker için ya Redis-backed state aktif ya da tek-worker garantisi belgeli ve uygulanmış.
- [ ] README/operasyon dokümanı production güvenlik env ayarlarını içeriyor.
