import json
import random
from pathlib import Path
from uuid import uuid4

from fastapi.templating import Jinja2Templates

from app.core.config import settings


def safe_upload_path(prefix: str, suffix: str = "", default_suffix: str = "") -> Path:
    """Return a UUID-based temp path that never uses user supplied filenames."""
    selected_suffix = suffix if suffix.startswith(".") else default_suffix
    clean_suffix = (
        selected_suffix
        if selected_suffix.startswith(".")
        and "/" not in selected_suffix
        and "\\" not in selected_suffix
        else ""
    )
    return settings.TEMP_DIR / f"{prefix}_{uuid4().hex}{clean_suffix}"


def resolve_temp_file(filename: str) -> Path | None:
    """Resolve a temp download name and enforce TEMP_DIR containment."""
    requested_name = Path(filename).name
    if requested_name != filename or requested_name in {"", ".", ".."}:
        return None

    candidate = (settings.TEMP_DIR / requested_name).resolve()
    temp_dir = settings.TEMP_DIR.resolve()
    try:
        is_inside = candidate.is_relative_to(temp_dir)
    except ValueError:
        is_inside = False
    if not is_inside or candidate.parent != temp_dir:
        return None
    return candidate


def get_random_tech_trivia() -> str:
    """Returns a random interesting tech fact in Turkish."""
    facts = [
        "İlk webcam, Cambridge Üniversitesi'ndeki bir kahve makinesini izlemek için icat edildi.",
        "İlk bilgisayar faresi ahşaptan yapılmıştı.",
        "Python ismi yılandan değil, Monty Python grubundan gelir.",
        "Dünyadaki ilk web sitesi hala yayındadır (info.cern.ch).",
        "QWERTY klavye düzeni, daktilo tuşlarının sıkışmasını önlemek için tasarlandı.",
        "Her gün yaklaşık 300 milyar e-posta gönderiliyor.",
        "Google'ın orijinal adı 'Backrub' idi.",
        "İlk 1GB hard disk 1980'de çıktı, 250 kg ağırlığındaydı ve 40.000 dolardı.",
        "İnternetin babası Vint Cerf, aynı zamanda işitme engellidir.",
        "NASA'nın internet hızı 91 GB/s'dir.",
    ]
    return random.choice(facts)


def get_tool_templates(tool_file_path: str) -> Jinja2Templates:
    """
    Creates a Jinja2Templates instance for a specific tool.
    Includes the tool's templates directory and the global templates directory.
    Automatically adds settings to Jinja2 globals for SEO.
    """
    tool_dir = Path(tool_file_path).resolve().parent
    templates = Jinja2Templates(
        directory=[
            str(tool_dir / "templates"),
            str(settings.BASE_DIR / "app" / "templates"),
        ]
    )
    templates.env.globals["settings"] = settings
    templates.env.filters["tojson"] = json.dumps

    return templates
