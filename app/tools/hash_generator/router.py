"""
Hash Generator Tool - Hash Üretici

Metin ve dosyalar için hash üretici.
Desteklenen algoritmalar: MD5, SHA1, SHA256, SHA512, BLAKE2b
"""

import hashlib
import time

from fastapi import APIRouter, Depends, File, Form, Request, UploadFile
from fastapi.responses import HTMLResponse

from app.core.config import settings
from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# Router
router = APIRouter(
    prefix="/tools/hash-generator",
    tags=["Hash Generator"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Supported algorithms
ALGORITHMS = {
    "md5": {"name": "MD5", "bits": 128, "description": "Hızlı ama güvenli değil (eski sistemler için)"},
    "sha1": {"name": "SHA-1", "bits": 160, "description": "Artık güvenli değil (eski uyumluluk için)"},
    "sha256": {"name": "SHA-256", "bits": 256, "description": "Standart güvenlik (önerilen)"},
    "sha512": {"name": "SHA-512", "bits": 512, "description": "Yüksek güvenlik"},
    "blake2b": {"name": "BLAKE2b", "bits": 512, "description": "Modern ve hızlı"},
}

# Tool Registration
tool_info = ToolInfo(
    slug="hash-generator",
    title="Hash Üretici",
    category=Category.SECURITY,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z"></path></svg>',
    description="Metin ve dosyalar için hash üretici. MD5, SHA-1, SHA-256, SHA-512, BLAKE2b.",
    short_description="MD5, SHA-256 ve daha fazlası",
    detailed_description="Dosya bütünlüğü kontrolü ve güvenli hash üretimi için profesyonel araç.",
    seo_title="Online Hash Generator | MD5, SHA-256 Calculator | İsviçre Çakısı",
    seo_description="Ücretsiz online hash üretici. MD5, SHA-1, SHA-256, SHA-512, BLAKE2b. Metin ve dosya hash hesaplama. Dosya bütünlüğü kontrolü.",
    keywords="hash generator, md5, sha256, sha512, blake2, checksum, dosya doğrulama",
    long_description="""
Hash Üretici, metin ve dosyalarınız için kriptografik hash değerleri hesaplayan güvenlik aracıdır.

**Desteklenen Algoritmalar:**
- **MD5**: 128-bit, hızlı ama çakışma saldırılarına karşı savunmasız
- **SHA-1**: 160-bit, artık güvenli kabul edilmiyor
- **SHA-256**: 256-bit, günümüzün standardı, blockchain ve SSL'de kullanılır
- **SHA-512**: 512-bit, maksimum güvenlik
- **BLAKE2b**: Modern, SHA-3 finalistlerinden, çok hızlı

**Kullanım Alanları:**
Dosya indirme doğrulaması, veri bütünlüğü kontrolü, şifre hashleme (sadece SHA-256+).
    """.strip(),
    use_cases=[
        "İndirilen dosyanın orijinal olup olmadığını kontrol etme",
        "İki dosyanın aynı içeriğe sahip olup olmadığını doğrulama",
        "Veri bütünlüğü kontrolü (backup verification)",
        "Blockchain ve merkle tree hesaplamaları",
        "Dosya parmak izi (fingerprint) oluşturma",
    ],
    faq=[
        {
            "question": "Hangi hash algoritmasını kullanmalıyım?",
            "answer": "Güvenlik için SHA-256 veya SHA-512 öneriyoruz. MD5 ve SHA-1 sadece eski sistem uyumluluğu için kullanın.",
        },
        {
            "question": "Hash'ten orijinal veriyi geri alabilir miyim?",
            "answer": "Hayır, hash fonksiyonları tek yönlüdür. Hash değerinden orijinal veriyi hesaplamak matematiksel olarak imkansızdır.",
        },
        {
            "question": "Neden iki farklı dosyanın aynı hash'i olabilir?",
            "answer": "Buna 'collision' denir ve teorik olarak mümkündür. SHA-256 için pratik olarak imkansızdır.",
        },
    ],
    accepts_text=True,
    accepts_files=True,
    max_upload_mb=50,
)

ToolRegistry.register(tool_info, router)


def calculate_hash(data: bytes, algorithm: str) -> str:
    """Calculate hash of data using specified algorithm."""
    if algorithm == "blake2b":
        hasher = hashlib.blake2b()
    else:
        hasher = hashlib.new(algorithm)
    hasher.update(data)
    return hasher.hexdigest()


def calculate_all_hashes(data: bytes) -> dict[str, str]:
    """Calculate all supported hashes for data."""
    return {algo: calculate_hash(data, algo) for algo in ALGORITHMS.keys()}


@router.get("/", response_class=HTMLResponse)
async def hash_generator_page(request: Request):
    """Render hash generator page."""
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={
            "tool": tool_info,
            "algorithms": ALGORITHMS,
        },
    )


@router.post("/text", response_class=HTMLResponse)
async def hash_text(
    request: Request,
    text: str = Form(...),
    algorithm: str = Form("all"),
):
    """Generate hash from text input."""
    start = time.time()

    try:
        if not text:
            return templates.TemplateResponse(
                request=request,
                name="partials/error.html",
                context={"error": "Lütfen bir metin girin."},
            )

        data = text.encode("utf-8")

        if algorithm == "all":
            hashes = calculate_all_hashes(data)
        else:
            if algorithm not in ALGORITHMS:
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={"error": f"Geçersiz algoritma: {algorithm}"},
                )
            hashes = {algorithm: calculate_hash(data, algorithm)}

        log_tool_call(
            "hash-generator", "success", (time.time() - start) * 1000, {"source": "text", "algorithm": algorithm}
        )

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "hashes": hashes,
                "algorithms": ALGORITHMS,
                "source": "text",
                "input_size": len(data),
            },
        )

    except Exception as e:
        log_tool_call("hash-generator", "error", (time.time() - start) * 1000, {"error": str(e)})
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )


@router.post("/file", response_class=HTMLResponse)
async def hash_file(
    request: Request,
    file: UploadFile = File(...),
    algorithm: str = Form("all"),
):
    """Generate hash from file upload."""
    start = time.time()

    try:
        # Read file
        contents = await file.read()

        # Check size
        max_size = (tool_info.max_upload_mb or settings.MAX_UPLOAD_SIZE_MB) * 1024 * 1024
        if len(contents) > max_size:
            return templates.TemplateResponse(
                request=request,
                name="partials/error.html",
                context={"error": f"Dosya çok büyük. Maksimum: {tool_info.max_upload_mb} MB"},
            )

        if algorithm == "all":
            hashes = calculate_all_hashes(contents)
        else:
            if algorithm not in ALGORITHMS:
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={"error": f"Geçersiz algoritma: {algorithm}"},
                )
            hashes = {algorithm: calculate_hash(contents, algorithm)}

        log_tool_call(
            "hash-generator",
            "success",
            (time.time() - start) * 1000,
            {"source": "file", "algorithm": algorithm, "size": len(contents)},
        )

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "hashes": hashes,
                "algorithms": ALGORITHMS,
                "source": "file",
                "filename": file.filename,
                "input_size": len(contents),
            },
        )

    except Exception as e:
        log_tool_call("hash-generator", "error", (time.time() - start) * 1000, {"error": str(e)})
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )


@router.post("/compare", response_class=HTMLResponse)
async def compare_hash(
    request: Request,
    hash1: str = Form(...),
    hash2: str = Form(...),
):
    """Compare two hash values."""
    start = time.time()

    try:
        hash1 = hash1.strip().lower()
        hash2 = hash2.strip().lower()

        match = hash1 == hash2

        log_tool_call("hash-generator", "success", (time.time() - start) * 1000, {"action": "compare", "match": match})

        return templates.TemplateResponse(
            request=request,
            name="partials/compare_result.html",
            context={
                "hash1": hash1,
                "hash2": hash2,
                "match": match,
            },
        )

    except Exception as e:
        log_tool_call("hash-generator", "error", (time.time() - start) * 1000, {"error": str(e)})
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )
