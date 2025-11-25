"""
Lorem Ipsum Generator Tool - Metin Üretici

Tasarım ve testler için rastgele metin üretici.
Paragraf, cümle ve kelime bazlı üretim.
"""

import random
import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# Router
router = APIRouter(
    prefix="/tools/lorem-ipsum",
    tags=["Lorem Ipsum"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Tool Registration
tool_info = ToolInfo(
    slug="lorem-ipsum",
    title="Lorem Ipsum",
    category=Category.DESIGN,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h7"></path></svg>',
    description="Tasarım ve testler için rastgele metin üretici. Paragraf, cümle, kelime.",
    short_description="Rastgele metin üretici",
    detailed_description="Web tasarımcıları ve editörler için profesyonel Lorem Ipsum üretici.",
    seo_title="Online Lorem Ipsum Generator | Türkçe Metin Üretici | İsviçre Çakısı",
    seo_description="Ücretsiz online Lorem Ipsum üretici. Paragraf, cümle ve kelime bazlı rastgele metin oluşturun. Tasarım ve testler için ideal.",
    keywords="lorem ipsum, metin üretici, dummy text, placeholder text, rastgele yazı",
    long_description="""
Lorem Ipsum Üretici, tasarımlarınızda kullanabileceğiniz anlamsız yer tutucu metinler oluşturur.

**Özellikler:**
- **Esnek Üretim:** Paragraf, cümle veya kelime sayısına göre üretim.
- **HTML Formatı:** İsterseniz <p> etiketleri ile HTML çıktısı alın.
- **Başlangıç Seçeneği:** Standart "Lorem ipsum dolor sit amet..." ile başlama seçeneği.

**Neden Kullanılır?**
Tasarım aşamasında içeriğin dikkat dağıtmasını önlemek ve yazı tipinin/düzenin nasıl görüneceğini test etmek için kullanılır.
    """.strip(),
    use_cases=[
        "Web sitesi tasarımlarında yer tutucu metin olarak",
        "Font ve tipografi testlerinde",
        "Veritabanı doluluk testlerinde",
        "Dergi ve gazete mizanpajlarında",
    ],
)

ToolRegistry.register(tool_info, router)

# Data
WORDS = [
    "lorem", "ipsum", "dolor", "sit", "amet", "consectetur", "adipiscing", "elit",
    "sed", "do", "eiusmod", "tempor", "incididunt", "ut", "labore", "et", "dolore",
    "magna", "aliqua", "ut", "enim", "ad", "minim", "veniam", "quis", "nostrud",
    "exercitation", "ullamco", "laboris", "nisi", "ut", "aliquip", "ex", "ea",
    "commodo", "consequat", "duis", "aute", "irure", "dolor", "in", "reprehenderit",
    "in", "voluptate", "velit", "esse", "cillum", "dolore", "eu", "fugiat", "nulla",
    "pariatur", "excepteur", "sint", "occaecat", "cupidatat", "non", "proident",
    "sunt", "in", "culpa", "qui", "officia", "deserunt", "mollit", "anim", "id",
    "est", "laborum", "sed", "ut", "perspiciatis", "unde", "omnis", "iste", "natus",
    "error", "sit", "voluptatem", "accusantium", "doloremque", "laudantium",
    "totam", "rem", "aperiam", "eaque", "ipsa", "quae", "ab", "illo", "inventore",
    "veritatis", "et", "quasi", "architecto", "beatae", "vitae", "dicta", "sunt",
    "explicabo", "nemo", "enim", "ipsam", "voluptatem", "quia", "voluptas", "sit",
    "aspernatur", "aut", "odit", "aut", "fugit", "sed", "quia", "consequuntur",
    "magni", "dolores", "eos", "qui", "ratione", "voluptatem", "sequi", "nesciunt",
]


def generate_sentence() -> str:
    """Generate a random sentence."""
    length = random.randint(5, 15)
    sentence = " ".join(random.choices(WORDS, k=length))
    return sentence.capitalize() + "."


def generate_paragraph() -> str:
    """Generate a random paragraph."""
    length = random.randint(3, 8)
    return " ".join(generate_sentence() for _ in range(length))


@router.get("/", response_class=HTMLResponse)
async def lorem_ipsum_page(request: Request):
    """Render lorem ipsum page."""
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={"tool": tool_info},
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_text(
    request: Request,
    count: int = Form(5),
    type: str = Form("paragraphs"),
    start_with_lorem: bool = Form(True),
    html_tags: bool = Form(False),
):
    """Generate lorem ipsum text."""
    start = time.time()

    try:
        # Limits
        if count < 1:
            count = 1
        if count > 100:
            count = 100

        result = []
        
        if type == "paragraphs":
            for _ in range(count):
                result.append(generate_paragraph())
        elif type == "sentences":
            for _ in range(count):
                result.append(generate_sentence())
        elif type == "words":
            result = random.choices(WORDS, k=count)
        
        # Start with standard text if requested
        if start_with_lorem and type == "paragraphs" and count > 0:
            standard = "Lorem ipsum dolor sit amet, consectetur adipiscing elit."
            if len(result) > 0:
                # Replace beginning of first paragraph
                first = result[0]
                # Simple heuristic: replace first sentence or prepend
                if "." in first:
                    parts = first.split(".", 1)
                    result[0] = standard + parts[1] if len(parts) > 1 else standard
                else:
                    result[0] = standard + " " + first

        log_tool_call("lorem-ipsum", "success", (time.time() - start) * 1000, {"count": count, "type": type})

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "text_parts": result,
                "type": type,
                "html_tags": html_tags,
            },
        )

    except Exception as e:
        log_tool_call("lorem-ipsum", "error", (time.time() - start) * 1000, {"error": str(e)})
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )
