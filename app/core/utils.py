import os
import random

from fastapi.templating import Jinja2Templates

from app.core.config import settings


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
    """
    tool_dir = os.path.dirname(os.path.abspath(tool_file_path))
    return Jinja2Templates(
        directory=[
            os.path.join(tool_dir, "templates"),
            os.path.join(settings.BASE_DIR, "app", "templates"),
        ]
    )
