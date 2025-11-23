# Katkıda Bulunma Rehberi (Contributing Guide)

İsviçre Çakısı projesine katkıda bulunmak istediğiniz için teşekkürler! Bu proje **Modular Monolith** mimarisi ve **Registry Pattern** kullanılarak geliştirilmiştir. Yeni bir araç eklemek veya mevcut bir aracı düzenlemek için aşağıdaki yönergeleri takip edebilirsiniz.

## 🏗 Proje Mimarisi

Proje, her aracın kendi izole klasöründe yaşadığı modüler bir yapıya sahiptir.

```
app/
├── main.py              # Giriş noktası (Auto-discovery burada çalışır)
├── core/                # Global ayarlar, utils, güvenlik
├── templates/           # Global şablonlar (layout.html vb.)
└── tools/               # ARAÇLAR BURADA
    ├── registry.py      # Araç kayıt sistemi (ToolRegistry)
    ├── image_converter/ # Örnek Araç
    │   ├── router.py    # FastAPI router ve mantık
    │   ├── utils.py     # Araca özel yardımcı fonksiyonlar
    │   └── templates/   # Araca özel HTML şablonları
    └── ...
```

## 🚀 Yeni Araç Ekleme (Adım Adım)

Yeni bir araç eklemek için (örneğin: `text-counter`):

### 1. Klasör Oluşturun

`app/tools/text_counter/` klasörünü oluşturun.

### 2. Router ve Mantık (`router.py`)

`app/tools/text_counter/router.py` dosyasını oluşturun ve şu yapıyı kullanın:

```python
from fastapi import APIRouter, Request, Depends
from fastapi.responses import HTMLResponse
from app.tools.registry import ToolRegistry, ToolInfo, Category
from app.core.utils import get_tool_templates

router = APIRouter(prefix="/tools/text-counter")
templates = get_tool_templates(__file__)

# Aracı Kaydet
tool_info = ToolInfo(
    slug="text-counter",
    title="Kelime Sayacı",
    category=Category.OTHER,
    icon="<svg>...</svg>",
    description="Metin içindeki kelime ve karakterleri sayar.",
    # ... diğer SEO ve detay alanları
)
ToolRegistry.register(tool_info, router)

@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    return templates.TemplateResponse(request=request, name="index.html", context={"tool": tool_info})
```

### 3. Şablonlar (`templates/`)

`app/tools/text_counter/templates/index.html` dosyasını oluşturun. `base.html`'den türetmeyi unutmayın.

```html
{% extends "layout.html" %} {% block content %}
<!-- Araç arayüzü -->
{% endblock %}
```

### 4. Test Edin

Uygulamayı başlatın. `main.py` içindeki auto-discovery mekanizması yeni aracınızı otomatik olarak bulacak ve ana sayfaya ekleyecektir.

## 📝 Kodlama Standartları (Vibe Coding Rules)

1.  **Dil:** Kodlar ve yorumlar **İngilizce**, ancak kullanıcı arayüzü (UI), loglar ve hata mesajları **Türkçe** olmalıdır.
2.  **Tip Güvenliği:** Python 3.13+ type hinting kullanılmalıdır.
3.  **Paket Yönetimi:** Sadece `uv` kullanın. (`uv add package_name`)
4.  **Frontend:** Karmaşık JS frameworkleri yerine **HTMX** ve **Alpine.js** kullanın.
5.  **Güvenlik:** Dosya yüklemelerinde her zaman `puremagic` ile magic-byte kontrolü yapın. Asla sadece dosya uzantısına güvenmeyin.
6.  **Hata Yönetimi:** Kullanıcıya asla "Internal Server Error" (500) sayfası göstermeyin. Hataları yakalayın ve anlamlı HTML parçaları (partials) döndürün.

## 🧪 Testler

Değişikliklerinizi göndermeden önce testleri çalıştırın:

```bash
uv run pytest
```
