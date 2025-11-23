# İsviçre Çakısı (Swiss Army Knife) 🛠️

Modern, hızlı ve çok amaçlı web tabanlı araç seti. Geliştiriciler, tasarımcılar ve günlük kullanıcılar için pratik çözümler sunar.

![İsviçre Çakısı](https://via.placeholder.com/1200x600?text=Isvicre+Cakisi)

## 🚀 Özellikler

- **Modern Teknoloji Yığını:** Python 3.13+, FastAPI, HTMX, Alpine.js ve Tailwind CSS.
- **Modüler Mimari:** "Registry Pattern" ile kolayca genişletilebilir yapı.
- **Hızlı ve Güvenli:** `uv` paket yöneticisi, rate limiting ve `puremagic` ile dosya güvenliği.
- **Kapsamlı Araçlar:** Medya, geliştirici ve güvenlik araçları tek bir yerde.
- **Kolay Kurulum:** Docker veya yerel ortamda hızlıca çalıştırılabilir.

## 🛠 Araçlar (Tools)

### Medya Araçları

- **Resim Dönüştürücü:** PNG, JPEG, WEBP formatları arasında dönüşüm.
- **Resim Boyutlandırıcı:** Resimleri yeniden boyutlandırma ve optimize etme.
- **Resim Kırpıcı:** Görselleri istenilen oranlarda kırpma.
- **Resim Metadata (EXIF):** Resim bilgilerini görüntüleme ve temizleme.
- **PDF Birleştirici:** Birden fazla PDF dosyasını tek bir dosyada birleştirme.
- **PDF Ayırıcı:** PDF dosyalarını sayfalara ayırma.
- **QR Kod Oluşturucu:** Özelleştirilebilir QR kodlar üretme.
- **QR Kod Okuyucu:** Resimden QR kod içeriğini okuma.

### Geliştirici Araçları

- **JSON Formatlayıcı:** JSON verilerini doğrulama ve güzelleştirme.
- **Base64 Dönüştürücü:** Metin ve dosyaları Base64 formatına çevirme.
- **URL Kodlayıcı:** URL encoding/decoding işlemleri.
- **Markdown Önizleme:** Canlı Markdown editörü ve HTML önizleme.

### Güvenlik Araçları

- **Şifre Oluşturucu:** Güçlü ve güvenli rastgele şifreler oluşturma.

## 🏗 Mimari

Proje **Modular Monolith** yapısındadır. Her araç `app/tools/` altında kendi izole klasöründe yaşar ve `app/tools/registry.py` üzerinden sisteme kaydolur.

- **Backend:** FastAPI (Async/Await)
- **Frontend:** HTMX + Jinja2 (SSR) + Alpine.js
- **Styling:** TailwindCSS
- **Package Manager:** `uv`

## 💻 Kurulum ve Çalıştırma

### Gereksinimler

- Python 3.13+
- uv (Modern Python paket yöneticisi)

### Yerel Geliştirme

```bash
# Projeyi klonlayın
git clone https://github.com/username/isvicre-cakisi.git
cd isvicre-cakisi

# Bağımlılıkları yükleyin
uv sync

# Uygulamayı başlatın
uv run uvicorn app.main:app --reload
```

Uygulama `http://localhost:8000` adresinde çalışacaktır.

### Docker ile Çalıştırma

```bash
docker build -t isvicre-cakisi .
docker run -p 8000:8000 isvicre-cakisi
```

## 🧪 Testler

Tüm testleri çalıştırmak için:

```bash
uv run pytest
```

## 📝 Lisans

Bu proje MIT lisansı ile lisanslanmıştır.
