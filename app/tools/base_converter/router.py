"""
Number Base Converter Tool - Taban Dönüştürücü

Sayı tabanları arasında dönüşüm yapar.
Desteklenen tabanlar: Binary (2), Octal (8), Decimal (10), Hexadecimal (16).
"""

import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# Router
router = APIRouter(
    prefix="/tools/base-converter",
    tags=["Base Converter"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Tool Registration
tool_info = ToolInfo(
    slug="base-converter",
    title="Taban Dönüştürücü",
    category=Category.DEV,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 7h6m0 10v-3m-3 3h.01M9 17h.01M9 14h.01M12 14h.01M15 11h.01M12 11h.01M9 11h.01M7 21h10a2 2 0 002-2V5a2 2 0 00-2-2H7a2 2 0 00-2 2v14a2 2 0 002 2z"></path></svg>',
    image_url="/static/images/base_converter.png",
    description="Sayı tabanları arasında dönüşüm. Binary, Octal, Decimal, Hexadecimal.",
    short_description="Binary, Hex, Decimal dönüştürücü",
    detailed_description="Geliştiriciler ve öğrenciler için sayı tabanı dönüştürme aracı.",
    seo_title="Online Number Base Converter | Binary to Decimal | İsviçre Çakısı",
    seo_description="Ücretsiz online taban dönüştürücü. Binary (2), Octal (8), Decimal (10) ve Hexadecimal (16) arasında anında dönüşüm yapın.",
    keywords="base converter, taban dönüştürücü, binary to decimal, hex to decimal, decimal to binary, sayı sistemleri",
    long_description="""
Taban Dönüştürücü, farklı sayı sistemleri arasında hızlı ve hatasız dönüşüm yapmanızı sağlar.

**Desteklenen Tabanlar:**
- **Binary (2):** 0 ve 1 (Bilgisayar dili)
- **Octal (8):** 0-7 arası rakamlar
- **Decimal (10):** Günlük hayatta kullandığımız onluk sistem
- **Hexadecimal (16):** 0-9 ve A-F (Web renkleri, bellek adresleri)

**Özellikler:**
- Anlık dönüşüm
- Büyük sayı desteği
- Hatalı giriş kontrolü
    """.strip(),
    use_cases=[
        "Bilgisayar bilimleri ödevleri",
        "Düşük seviyeli programlama (Assembly, C)",
        "Ağ maskesi hesaplamaları",
        "Renk kodu analizleri",
    ],
)

ToolRegistry.register(tool_info, router)


@router.get("/", response_class=HTMLResponse)
async def base_converter_page(request: Request):
    """Render base converter page."""
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={"tool": tool_info},
    )


@router.post("/convert", response_class=HTMLResponse)
async def convert_base(
    request: Request,
    value: str = Form(...),
    from_base: int = Form(...),
):
    """Convert number from one base to all others."""
    start = time.time()

    try:
        value = value.strip()
        if not value:
            return templates.TemplateResponse(
                request=request,
                name="partials/error.html",
                context={"error": "Lütfen bir sayı girin."},
            )

        # Parse input to decimal first
        try:
            decimal_value = int(value, from_base)
        except ValueError:
            return templates.TemplateResponse(
                request=request,
                name="partials/error.html",
                context={
                    "error": f"Girdiğiniz değer {from_base} tabanına uygun değil."
                },
            )

        # Convert to all bases
        results = {
            "binary": bin(decimal_value)[2:],  # Remove '0b' prefix
            "octal": oct(decimal_value)[2:],  # Remove '0o' prefix
            "decimal": str(decimal_value),
            "hexadecimal": hex(decimal_value)[
                2:
            ].upper(),  # Remove '0x' prefix and uppercase
        }

        log_tool_call(
            "base-converter",
            "success",
            (time.time() - start) * 1000,
            {"from_base": from_base, "value": value},
        )

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "results": results,
                "input_value": value,
                "from_base": from_base,
            },
        )

    except Exception as e:
        log_tool_call(
            "base-converter", "error", (time.time() - start) * 1000, {"error": str(e)}
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )
