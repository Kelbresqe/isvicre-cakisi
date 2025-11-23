"""
Common upload pipeline with security validation.
Provides centralized file validation for all tools.
"""

from io import BytesIO
from pathlib import Path

import puremagic
from fastapi import HTTPException, UploadFile
from PIL import Image
from pypdf import PdfReader

from app.core.config import settings


# Custom Exceptions
class InvalidFileError(Exception):
    """Base exception for invalid files."""

    pass


class UnsupportedMimeTypeError(InvalidFileError):
    """Raised when MIME type is not allowed."""

    pass


class FileTooLargeError(InvalidFileError):
    """Raised when file exceeds size limit."""

    pass


class InvalidImageError(InvalidFileError):
    """Raised when image file is corrupted or invalid."""

    pass


class InvalidPDFError(InvalidFileError):
    """Raised when PDF file is corrupted or invalid."""

    pass


async def validate_file(file: UploadFile, max_size_mb: int, allowed_mimes: set[str]) -> bytes:
    """
    Validates file size and MIME type.
    Returns the file content as bytes.
    """
    # 1. Size Check
    file.file.seek(0, 2)
    size = file.file.tell()
    file.file.seek(0)

    if size > max_size_mb * 1024 * 1024:
        raise HTTPException(
            status_code=413,
            detail=f"Dosya boyutu çok büyük. Maksimum {max_size_mb}MB yükleyebilirsiniz.",
        )

    content = await file.read()

    # 2. Magic Bytes Check
    try:
        mime = puremagic.from_string(content, mime=True)
        if mime not in allowed_mimes:
            raise HTTPException(
                status_code=400,
                detail=f"Desteklenmeyen dosya türü: {mime}. İzin verilenler: {', '.join(allowed_mimes)}",
            )
    except puremagic.PureError:
        raise HTTPException(status_code=400, detail="Dosya türü belirlenemedi.")

    return content


async def validate_and_load_image(file: UploadFile) -> tuple[Image.Image, str, int]:
    """
    Validates and loads an image using Pillow.
    Returns (Image object, filename, original_size).
    """
    content = await validate_file(file, settings.MAX_IMAGE_SIZE_MB, settings.ALLOWED_IMAGE_MIME_TYPES)

    try:
        img = Image.open(BytesIO(content))
        img.verify()  # Verify integrity
        img = Image.open(BytesIO(content))  # Re-open after verify

        return img, file.filename, len(content)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Geçersiz resim dosyası: {str(e)}")


async def validate_pdf(file: UploadFile) -> bytes:
    """
    Validates a PDF file.
    Returns file content as bytes.
    """
    content = await validate_file(file, settings.MAX_PDF_SIZE_MB, settings.ALLOWED_PDF_MIME_TYPES)

    # Additional PDF validation
    try:
        reader = PdfReader(BytesIO(content))
        if len(reader.pages) == 0:
            raise HTTPException(status_code=400, detail="PDF dosyası boş.")
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=400,
            detail="Geçersiz PDF dosyası. Lütfen geçerli bir PDF yükleyin.",
        )

    return content


def cleanup_temp_files(*paths: Path) -> None:
    """
    Cleans up temporary files safely.

    Args:
        *paths: Paths to files/directories to clean up
    """
    import shutil

    for path in paths:
        if not path or not path.exists():
            continue

        try:
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                shutil.rmtree(path)
        except Exception as e:
            # Log but don't raise - cleanup failures shouldn't break the app
            print(f"⚠️ Cleanup failed for {path}: {e}")
