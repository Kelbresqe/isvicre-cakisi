"""PDF Splitter tool"""

import time
import uuid

from fastapi import APIRouter, Depends, Form, Request, UploadFile
from fastapi.responses import FileResponse, HTMLResponse
from pypdf import PdfReader, PdfWriter

from app.core.config import settings
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry, ToolRelation

router = APIRouter(prefix="/tools/pdf-splitter", tags=["PDF Splitter"], dependencies=[Depends(rate_limit_dependency)])

templates = get_tool_templates(__file__)

tool_info = ToolInfo(
    slug="pdf-splitter",
    title="PDF Ayırıcı",
    category=Category.OFFICE,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path></svg>',
    image_url="/static/images/pdf_splitter.png",
    description="PDF dosyalarından istediğiniz sayfaları seçerek yeni PDF oluşturun.",
    short_description="PDF'den sayfa ayırma ve çıkarma aracı",
    seo_title="Ücretsiz PDF Ayırıcı - Sayfa Seçerek PDF Oluştur | İsviçre Çakısı",
    seo_description="PDF dosyalarınızdan istediğiniz sayfaları seçin, yeni PDF oluşturun. Sayfa aralıkları ile çalışır.",
    keywords="pdf ayırıcı, pdf splitter, pdf sayfa seçici",
    long_description="PDF dosyalarınızdan belirli sayfaları seçerek yeni PDF oluşturun. Sayfa aralıkları (1-5,7,9-12) formatında belirtin.",
    use_cases=["Büyük PDF'den sadece gerekli sayfaları ayırma", "Bölümlere ayırma"],
    faq=[{"question": "Sayfa formatı nasıl?", "answer": "1-5,7,9-12 formatında virgülle ayırın. Aralıklar tire ile."}],
    accepts_files=True,
    max_upload_mb=50,
    accepts_pipeline_files=True,
    produces_pipeline_files=True,
    suggested_next=[
        ToolRelation(
            slug="pdf-merger",
            relation_type="next",
            label="Birleştir",
            description="Ayırdığınız sayfaları yeniden birleştirin",
        )
    ],
)

ToolRegistry.register(tool_info, router)


def parse_pages(page_str: str, max_pages: int) -> list[int]:
    """Parse '1-3,5,7-9' to [1,2,3,5,7,8,9]"""
    pages = []
    for part in page_str.split(","):
        part = part.strip()
        if "-" in part:
            start, end = map(int, part.split("-"))
            pages.extend(range(start, end + 1))
        else:
            pages.append(int(part))
    return [p for p in pages if 1 <= p <= max_pages]


@router.get("/", response_class=HTMLResponse)
async def page(request: Request, pipeline_id: str | None = None):
    from app.core.observability import record_page_view

    record_page_view("pdf-splitter", request.headers.get("user-agent"), request.headers.get("referer"))

    pipeline_file = None
    if pipeline_id:
        from app.core.pipeline import resolve_pipeline_file

        pipeline_file = resolve_pipeline_file(pipeline_id)
        if pipeline_file and pipeline_file["mime_type"] != "application/pdf":
            pipeline_file = None

    return templates.TemplateResponse(
        request=request, name="splitter.html", context={"tool": tool_info, "pipeline_file": pipeline_file}
    )


@router.post("/split", response_class=FileResponse)
async def split(
    request: Request, file: UploadFile | None = None, pipeline_id: str | None = None, pages: str = Form(...)
):
    from app.core.observability import log_tool_call

    start = time.time()

    try:
        if pipeline_id:
            from app.core.pipeline import resolve_pipeline_file

            pf = resolve_pipeline_file(pipeline_id)
            if not pf:
                raise ValueError("Pipeline dosyası bulunamadı")
            file_path = pf["file_path"]
        else:
            if not file or file.content_type != "application/pdf":
                raise ValueError("Geçerli PDF gerekli")
            temp = settings.TEMP_DIR / f"split_in_{file.filename}"
            with open(temp, "wb") as f:
                f.write(await file.read())
            file_path = str(temp)

        reader = PdfReader(file_path)
        selected = parse_pages(pages, len(reader.pages))
        if not selected:
            raise ValueError("Geçerli sayfa numarası belirtilmedi")

        writer = PdfWriter()
        for page_num in selected:
            writer.add_page(reader.pages[page_num - 1])

        output = settings.TEMP_DIR / f"split_{uuid.uuid4().hex[:8]}.pdf"
        with open(output, "wb") as f:
            writer.write(f)

        # Pipeline
        if tool_info.produces_pipeline_files:
            from app.core.pipeline import create_pipeline_file

            try:
                create_pipeline_file("pdf-splitter", str(output), "application/pdf", output.name)
            except Exception:
                pass

        log_tool_call("pdf-splitter", "success", (time.time() - start) * 1000, {"pages": len(selected)})
        return FileResponse(path=output, filename=output.name, media_type="application/pdf")
    except Exception as e:
        log_tool_call("pdf-splitter", "error", (time.time() - start) * 1000, {"error": str(e)})
        raise
