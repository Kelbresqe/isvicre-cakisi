"""
Color Picker Tool - Renk Seçici ve Dönüştürücü

Renk formatları arasında dönüşüm yapar ve paletler oluşturur.
Desteklenen formatlar: HEX, RGB, HSL, CMYK
"""

import colorsys
import re
import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# Router
router = APIRouter(
    prefix="/tools/color-picker",
    tags=["Color Picker"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Tool Registration
tool_info = ToolInfo(
    slug="color-picker",
    title="Renk Seçici",
    category=Category.DESIGN,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01"></path></svg>',
    description="Renk kodlarını dönüştürün ve paletler oluşturun. HEX, RGB, HSL, CMYK.",
    short_description="HEX, RGB, HSL dönüştürücü",
    detailed_description="Tasarımcılar ve geliştiriciler için gelişmiş renk aracı. Format dönüşümü ve palet üretimi.",
    seo_title="Online Color Picker & Converter | HEX to RGB | İsviçre Çakısı",
    seo_description="Ücretsiz online renk seçici ve dönüştürücü. HEX, RGB, HSL, CMYK formatları arasında dönüşüm yapın. Renk paletleri oluşturun.",
    keywords="color picker, renk seçici, hex to rgb, rgb to hex, hsl converter, cmyk converter, renk paleti",
    long_description="""
Renk Seçici, web tasarımcıları ve geliştiriciler için kapsamlı bir renk yönetim aracıdır.

**Özellikler:**
- **Format Dönüşümü:** HEX, RGB, HSL ve CMYK arasında anında dönüşüm.
- **Renk Seçici:** Görsel renk seçici ile istediğiniz rengi bulun.
- **Palet Üretimi:** Seçilen renge uygun tamamlayıcı, analog ve monokromatik paletler.
- **Kontrast Kontrolü:** Metin ve arka plan uyumluluğu için basit kontrol.

**Desteklenen Formatlar:**
- **HEX:** #FF5733 (Web standardı)
- **RGB:** rgb(255, 87, 51) (Ekran renkleri)
- **HSL:** hsl(10, 100%, 60%) (İnsan algısına uygun)
- **CMYK:** cmyk(0, 66, 80, 0) (Baskı renkleri)
    """.strip(),
    use_cases=[
        "Web sitesi için renk kodu bulma",
        "HEX kodunu RGB'ye çevirme",
        "Baskı için CMYK karşılığını öğrenme",
        "Uyumlu renk paletleri oluşturma",
    ],
)

ToolRegistry.register(tool_info, router)


def hex_to_rgb(hex_color: str) -> tuple[int, ...]:
    """Convert HEX to RGB."""
    hex_color = hex_color.lstrip("#")
    if len(hex_color) == 3:
        hex_color = "".join([c * 2 for c in hex_color])
    return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(r: int, g: int, b: int) -> str:
    """Convert RGB to HEX."""
    return "#{:02x}{:02x}{:02x}".format(r, g, b)


def rgb_to_hsl(r: int, g: int, b: int) -> tuple[int, int, int]:
    """Convert RGB to HSL."""
    h, lightness, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    return int(h * 360), int(s * 100), int(lightness * 100)


def rgb_to_cmyk(r: int, g: int, b: int) -> tuple[int, int, int, int]:
    """Convert RGB to CMYK."""
    if (r, g, b) == (0, 0, 0):
        return 0, 0, 0, 100

    c = 1 - r / 255
    m = 1 - g / 255
    y = 1 - b / 255

    min_cmy = min(c, m, y)
    c = (c - min_cmy) / (1 - min_cmy)
    m = (m - min_cmy) / (1 - min_cmy)
    y = (y - min_cmy) / (1 - min_cmy)
    k = min_cmy

    return int(c * 100), int(m * 100), int(y * 100), int(k * 100)


def parse_color(color: str) -> tuple[int, ...] | None:
    """Parse color string to RGB tuple."""
    color = color.strip().lower()

    # HEX
    if re.match(r"^#?([0-9a-f]{3}|[0-9a-f]{6})$", color):
        return hex_to_rgb(color)

    # RGB
    rgb_match = re.match(r"^rgb\(\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*\)$", color)
    if rgb_match:
        return tuple(map(int, rgb_match.groups()))

    return None


@router.get("/", response_class=HTMLResponse)
async def color_picker_page(request: Request):
    """Render color picker page."""
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={"tool": tool_info},
    )


@router.post("/convert", response_class=HTMLResponse)
async def convert_color(
    request: Request,
    color: str = Form(...),
):
    """Convert color and generate palette."""
    start = time.time()

    try:
        rgb = parse_color(color)
        if not rgb:
            # Try to interpret as raw hex if no # provided and valid length
            if re.match(r"^[0-9a-f]{6}$", color):
                rgb = hex_to_rgb(f"#{color}")
            else:
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={
                        "error": "Geçersiz renk formatı. HEX (#FF0000) veya RGB (rgb(255,0,0)) kullanın."
                    },
                )

        r, g, b = rgb
        hex_val = rgb_to_hex(r, g, b)
        hsl = rgb_to_hsl(r, g, b)
        cmyk = rgb_to_cmyk(r, g, b)

        # Generate Palette
        h, s, lightness = hsl
        palette = {
            "complementary": [
                rgb_to_hex(
                    *map(
                        lambda x: int(x * 255),
                        colorsys.hls_to_rgb(
                            (h + 180) % 360 / 360, lightness / 100, s / 100
                        ),
                    )
                )
            ],
            "analogous": [
                rgb_to_hex(
                    *map(
                        lambda x: int(x * 255),
                        colorsys.hls_to_rgb(
                            (h - 30) % 360 / 360, lightness / 100, s / 100
                        ),
                    )
                ),
                rgb_to_hex(
                    *map(
                        lambda x: int(x * 255),
                        colorsys.hls_to_rgb(
                            (h + 30) % 360 / 360, lightness / 100, s / 100
                        ),
                    )
                ),
            ],
            "monochromatic": [
                rgb_to_hex(
                    *map(
                        lambda x: int(x * 255),
                        colorsys.hls_to_rgb(
                            h / 360, max(0, lightness - 20) / 100, s / 100
                        ),
                    )
                ),
                rgb_to_hex(
                    *map(
                        lambda x: int(x * 255),
                        colorsys.hls_to_rgb(
                            h / 360, min(100, lightness + 20) / 100, s / 100
                        ),
                    )
                ),
            ],
        }

        log_tool_call(
            "color-picker",
            "success",
            (time.time() - start) * 1000,
            {"color": color, "hex": hex_val},
        )

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "hex": hex_val,
                "rgb": f"rgb({r}, {g}, {b})",
                "hsl": f"hsl({h}, {s}%, {lightness}%)",
                "cmyk": f"cmyk({cmyk[0]}%, {cmyk[1]}%, {cmyk[2]}%, {cmyk[3]}%)",
                "r": r,
                "g": g,
                "b": b,
                "palette": palette,
            },
        )

    except Exception as e:
        log_tool_call(
            "color-picker", "error", (time.time() - start) * 1000, {"error": str(e)}
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )
