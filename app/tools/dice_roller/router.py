"""
Dice Roller Tool - Zar Atıcı

D&D ve masa oyunları için zar atma aracı.
Desteklenen zarlar: D4, D6, D8, D10, D12, D20, D100
Notation desteği: 2d6+3, 1d20-2, 4d6kh3 (keep highest 3)
"""

import random
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
    prefix="/tools/dice-roller",
    tags=["Dice Roller"],
    dependencies=[Depends(rate_limit_dependency)],
)

# Templates
templates = get_tool_templates(__file__)

# Tool Registration
tool_info = ToolInfo(
    slug="dice-roller",
    title="Zar Atıcı",
    category=Category.GAME,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M20 7l-8-4-8 4m16 0l-8 4m8-4v10l-8 4m0-10L4 7m8 4v10M4 7v10l8 4"></path></svg>',
    image_url="/static/images/dice_roller.png",
    description="D&D ve masa oyunları için zar atma aracı. D4'ten D100'e tüm zarlar.",
    short_description="D4-D100 zarları, çoklu zar atışı",
    detailed_description="Dungeons & Dragons ve diğer masa oyunları için profesyonel zar atıcı.",
    seo_title="Online Zar Atıcı | D&D Dice Roller | İsviçre Çakısı",
    seo_description="Ücretsiz online zar atma aracı. D4, D6, D8, D10, D12, D20, D100 zarları. 2d6+3 gibi notation desteği. D&D ve masa oyunları için ideal.",
    keywords="zar atıcı, dice roller, d20, d&d, dungeons dragons, masa oyunu, rpg",
    long_description="""
Zar Atıcı, masa oyuncuları ve RPG severler için tasarlanmış profesyonel bir zar simülatörüdür.

**Desteklenen Zarlar:**
D4, D6, D8, D10, D12, D20 ve D100 (percentile) zarları dahil tüm standart polyhedral zarları destekler.

**Dice Notation:**
Standart zar notasyonu ile karmaşık atışlar yapabilirsiniz: 2d6+3 (2 adet D6 at, +3 ekle), 
4d6kh3 (4 D6 at, en yüksek 3'ü tut), 1d20-2 (D20 at, 2 çıkar).

**Adil Sonuçlar:**
Kriptografik olmayan ama yüksek kaliteli rastgele sayı üreteci kullanılır. 
Her atış bağımsız ve önceki sonuçlardan etkilenmez.
    """.strip(),
    use_cases=[
        "D&D ve Pathfinder oyun oturumlarında zar atışları",
        "Board game geceleri için dijital zar",
        "RPG karakter oluşturma (4d6 drop lowest)",
        "Rastgele karar verme (D2 = yazı/tura)",
        "Matematik ve olasılık öğretimi",
    ],
    faq=[
        {
            "question": "Zarlar gerçekten rastgele mi?",
            "answer": "Evet, Python'un random modülü Mersenne Twister algoritması kullanır. Fiziksel zarlar kadar adildir.",
        },
        {
            "question": "2d6+3 ne demek?",
            "answer": "2 adet 6 yüzlü zar at ve sonuca 3 ekle. Örneğin: 4+5+3 = 12",
        },
        {
            "question": "D100 nasıl çalışır?",
            "answer": "1-100 arası rastgele sayı üretir. Genellikle 2 adet D10 (onlar ve birler) ile simüle edilir.",
        },
    ],
    accepts_text=True,
)

ToolRegistry.register(tool_info, router)

# Dice types
DICE_TYPES = {
    "d4": 4,
    "d6": 6,
    "d8": 8,
    "d10": 10,
    "d12": 12,
    "d20": 20,
    "d100": 100,
}

# Dice notation regex: 2d6+3, 1d20-2, 4d6kh3, etc.
DICE_NOTATION_PATTERN = re.compile(
    r"^(\d+)?d(\d+)(?:kh(\d+)|kl(\d+))?([+-]\d+)?$", re.IGNORECASE
)


def parse_dice_notation(notation: str) -> dict | None:
    """
    Parse dice notation like 2d6+3, 4d6kh3, 1d20-2

    Returns:
        dict with: count, sides, keep_highest, keep_lowest, modifier
    """
    notation = notation.lower().replace(" ", "")
    match = DICE_NOTATION_PATTERN.match(notation)

    if not match:
        return None

    count = int(match.group(1)) if match.group(1) else 1
    sides = int(match.group(2))
    keep_highest = int(match.group(3)) if match.group(3) else None
    keep_lowest = int(match.group(4)) if match.group(4) else None
    modifier = int(match.group(5)) if match.group(5) else 0

    # Validate
    if count < 1 or count > 100:
        return None
    if sides < 2 or sides > 1000:
        return None
    if keep_highest and keep_highest > count:
        return None
    if keep_lowest and keep_lowest > count:
        return None

    return {
        "count": count,
        "sides": sides,
        "keep_highest": keep_highest,
        "keep_lowest": keep_lowest,
        "modifier": modifier,
    }


def roll_dice(
    count: int,
    sides: int,
    keep_highest: int | None = None,
    keep_lowest: int | None = None,
    modifier: int = 0,
) -> dict:
    """
    Roll dice and return detailed results.
    """
    # Roll all dice
    rolls = [random.randint(1, sides) for _ in range(count)]
    original_rolls = rolls.copy()

    # Apply keep highest/lowest
    kept_rolls = rolls.copy()
    dropped_rolls = []

    if keep_highest:
        sorted_rolls = sorted(rolls, reverse=True)
        kept_rolls = sorted_rolls[:keep_highest]
        dropped_rolls = sorted_rolls[keep_highest:]
    elif keep_lowest:
        sorted_rolls = sorted(rolls)
        kept_rolls = sorted_rolls[:keep_lowest]
        dropped_rolls = sorted_rolls[keep_lowest:]

    # Calculate total
    subtotal = sum(kept_rolls)
    total = subtotal + modifier

    # Build expression string
    if count == 1:
        expr = str(rolls[0])
    else:
        expr = " + ".join(str(r) for r in kept_rolls)
        if dropped_rolls:
            expr += f" (dropped: {', '.join(str(r) for r in dropped_rolls)})"

    if modifier > 0:
        expr += f" + {modifier}"
    elif modifier < 0:
        expr += f" - {abs(modifier)}"

    expr += f" = {total}"

    return {
        "rolls": original_rolls,
        "kept": kept_rolls,
        "dropped": dropped_rolls,
        "subtotal": subtotal,
        "modifier": modifier,
        "total": total,
        "expression": expr,
        "is_critical": sides == 20 and count == 1 and total - modifier == 20,
        "is_fumble": sides == 20 and count == 1 and total - modifier == 1,
    }


@router.get("/", response_class=HTMLResponse)
async def dice_roller_page(request: Request):
    """Render dice roller page."""
    return templates.TemplateResponse(
        request=request,
        name="page.html",
        context={
            "tool": tool_info,
            "dice_types": list(DICE_TYPES.keys()),
        },
    )


@router.post("/roll", response_class=HTMLResponse)
async def roll(
    request: Request,
    notation: str = Form(None),
    dice_type: str = Form(None),
    count: int = Form(1),
    modifier: int = Form(0),
):
    """Handle dice roll request."""
    start = time.time()

    try:
        # Parse notation if provided
        if notation and notation.strip():
            parsed = parse_dice_notation(notation.strip())
            if not parsed:
                log_tool_call(
                    "dice-roller",
                    "error",
                    (time.time() - start) * 1000,
                    {"error": "invalid_notation"},
                )
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={"error": f"Geçersiz zar notasyonu: {notation}"},
                )

            result = roll_dice(
                count=parsed["count"],
                sides=parsed["sides"],
                keep_highest=parsed["keep_highest"],
                keep_lowest=parsed["keep_lowest"],
                modifier=parsed["modifier"],
            )
            notation_used = notation.strip()
        else:
            # Use individual fields
            if dice_type not in DICE_TYPES:
                log_tool_call(
                    "dice-roller",
                    "error",
                    (time.time() - start) * 1000,
                    {"error": "invalid_dice_type"},
                )
                return templates.TemplateResponse(
                    request=request,
                    name="partials/error.html",
                    context={"error": f"Geçersiz zar tipi: {dice_type}"},
                )

            sides = DICE_TYPES[dice_type]
            count = max(1, min(count, 100))  # Clamp between 1-100
            modifier = max(-1000, min(modifier, 1000))  # Clamp modifier

            result = roll_dice(count=count, sides=sides, modifier=modifier)

            # Build notation string
            notation_used = f"{count}{dice_type}"
            if modifier > 0:
                notation_used += f"+{modifier}"
            elif modifier < 0:
                notation_used += str(modifier)

        log_tool_call(
            "dice-roller",
            "success",
            (time.time() - start) * 1000,
            {"notation": notation_used},
        )

        return templates.TemplateResponse(
            request=request,
            name="partials/result.html",
            context={
                "result": result,
                "notation": notation_used,
            },
        )

    except Exception as e:
        log_tool_call(
            "dice-roller", "error", (time.time() - start) * 1000, {"error": str(e)}
        )
        return templates.TemplateResponse(
            request=request,
            name="partials/error.html",
            context={"error": f"Bir hata oluştu: {str(e)}"},
        )
