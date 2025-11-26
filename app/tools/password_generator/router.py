import secrets
import string
import time

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import HTMLResponse

from app.core.observability import log_tool_call
from app.core.rate_limit import rate_limit_dependency
from app.core.utils import get_tool_templates
from app.tools.registry import Category, ToolInfo, ToolRegistry

# 1. Router Tanımlama
router = APIRouter(
    prefix="/tools/password-generator",
    tags=["Password Generator"],
    dependencies=[Depends(rate_limit_dependency)],
)

# 2. Şablon Ayarları
templates = get_tool_templates(__file__)

# 3. Aracı Kaydetme (Registry)
tool_info = ToolInfo(
    slug="password-generator",
    title="Şifre Oluşturucu",
    category=Category.SECURITY,
    icon='<svg class="w-full h-full" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z"></path></svg>',
    image_url="/static/images/password_generator.png",
    description="Güvenli ve rastgele şifreler oluşturun.",
    short_description="Güçlü ve güvenli şifre üretimi",
    detailed_description="Kriptografik olarak güvenli rastgele şifreler oluşturun. Uzunluk, sayı, sembol ve harf seçeneklerini özelleştirin. Şifreleriniz sunucuda saklanmaz.",
    seo_title="Güvenli Şifre Oluşturucu - Password Generator | İsviçre Çakısı",
    seo_description="Güçlü ve kırılması zor şifreler oluşturun. Rastgele şifre üretici ile hesaplarınızı güvende tutun.",
    keywords="şifre oluşturucu, password generator, rastgele şifre, güçlü şifre, güvenli parola",
    long_description="""İsviçre Çakısı Şifre Oluşturucu, online hesaplarınızın güvenliğini artırmak için kriptografik olarak güvenli rastgele şifreler oluşturur. Python'un secrets modülü ile gerçek rastgelelik sağlanır, tahmin edilemez şifreler üretir.

4-128 karakter arasında istediğiniz uzunlukta şifre oluşturabilirsiniz. Büyük harf, küçük harf, rakam ve özel sembol kullanım seçenekleri ile her platformun gereksinimlerine uygun şifreler üretebilirsiniz.

Şifre gücü göstergesi, entropi hesabı ile şifrenizin ne kadar güvenli olduğunu görsel olarak sunar. Zayıf şifrelerden kaçının, güçlü şifre önerileri alın.

Oluşturduğunuz şifreler asla sunucuya gönderilmez veya kaydedilmez. Tek tıkla kopyalama özelliği ile şifrenizi hızlıca kullanıma hazır hale getirebilirsiniz.""",
    use_cases=[
        "Online bankacılık ve e-ticaret hesapları için güçlü şifreler oluşturun",
        "Wi-Fi modem şifrelerini güvenli hale getirin",
        "Kurumsal hesaplar için politika uyumlu şifreler üretin",
        "Veritabanı ve API key'leri için rastgele güvenli stringler oluşturun",
        "Şifre yöneticisi kullanırken her hesap için benzersiz şifreler üretin",
    ],
    faq=[
        {
            "question": "Şifrelerim kaydediliyor mu?",
            "answer": "Hayır. Şifre üretimi tamamen tarayıcınızda gerçekleşir ve sunucuya hiçbir veri gönderilmez. Gizliliğiniz tam olarak korunur.",
        },
        {
            "question": "Ne kadar uzun şifre kullanmalıyım?",
            "answer": "En az 12 karakter öner ilir. Önemli hesaplar için (banka, e-posta) 16+ karakter ve tüm karakter türlerini içeren şifreler kullanın.",
        },
        {
            "question": "Üretilen şifreler gerçekten rastgele mi?",
            "answer": "Evet, Python secrets modülü işletim sisteminin kriptografik rastgele sayı üretecini kullanır. Bu şifreler tahmin edilemez.",
        },
    ],
    # Tool capabilities
    accepts_files=False,
    accepts_text=True,
    max_upload_mb=None,
)

ToolRegistry.register(tool_info, router)


# 4. Endpointler
@router.get("/", response_class=HTMLResponse)
async def page(request: Request):
    # v0.7.0: Analytics tracking
    from app.core.observability import record_page_view

    record_page_view(
        "password-generator",
        request.headers.get("user-agent"),
        request.headers.get("referer"),
    )

    return templates.TemplateResponse(
        request=request, name="password_generator.html", context={"tool": tool_info}
    )


@router.post("/generate", response_class=HTMLResponse)
async def generate_password(
    request: Request,
    length: int = Form(16),
    use_uppercase: bool = Form(False),
    use_lowercase: bool = Form(True),
    use_numbers: bool = Form(True),
    use_symbols: bool = Form(False),
):
    start_time = time.time()
    try:
        # Validate length
        length = max(4, min(length, 128))

        # Build character set
        chars = ""
        if use_lowercase:
            chars += string.ascii_lowercase
        if use_uppercase:
            chars += string.ascii_uppercase
        if use_numbers:
            chars += string.digits
        if use_symbols:
            chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

        # Fallback if nothing selected
        if not chars:
            chars = string.ascii_lowercase + string.digits

        # Generate password
        password = "".join(secrets.choice(chars) for _ in range(length))

        # Calculate strength (simple entropy estimation)
        pool_size = len(chars)
        entropy = length * (pool_size.bit_length())

        strength_text = "Zayıf"
        strength_color = "text-red-400"
        strength_percent = 25

        if entropy > 120:
            strength_text = "Çok Güçlü"
            strength_color = "text-emerald-400"
            strength_percent = 100
        elif entropy > 80:
            strength_text = "Güçlü"
            strength_color = "text-green-400"
            strength_percent = 75
        elif entropy > 50:
            strength_text = "Orta"
            strength_color = "text-yellow-400"
            strength_percent = 50

        duration = (time.time() - start_time) * 1000
        log_tool_call("password-generator", "success", duration, {"length": length})

        return f"""
        <div class="bg-slate-800/50 rounded-2xl p-8 border border-slate-700/50 shadow-xl animate-fade-in">
            <div class="relative mb-6">
                <input type="text" readonly value="{password}" id="generated-password"
                       class="w-full bg-slate-900 border border-slate-700 rounded-xl p-4 text-2xl font-mono text-center text-white focus:ring-2 focus:ring-emerald-500 focus:border-transparent transition-all">
                
                <button onclick="navigator.clipboard.writeText(document.getElementById('generated-password').value); this.innerHTML = '<svg class=\'w-5 h-5\' fill=\'none\' stroke=\'currentColor\' viewBox=\'0 0 24 24\'><path stroke-linecap=\'round\' stroke-linejoin=\'round\' stroke-width=\'2\' d=\'M5 13l4 4L19 7\'></path></svg> Kopyalandı!';"
                        class="absolute right-2 top-2 bottom-2 px-4 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors flex items-center gap-2">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z"></path></svg>
                    Kopyala
                </button>
            </div>
            
            <div class="flex items-center justify-between text-sm mb-2">
                <span class="text-slate-400">Güç: <span class="{strength_color} font-bold">{strength_text}</span></span>
                <span class="text-slate-500">{entropy} bit entropi</span>
            </div>
            
            <div class="w-full bg-slate-700 rounded-full h-2">
                <div class="bg-gradient-to-r from-red-500 via-yellow-500 to-emerald-500 h-2 rounded-full transition-all duration-500" style="width: {strength_percent}%"></div>
            </div>
        </div>
        """
    except Exception as e:
        duration = (time.time() - start_time) * 1000
        log_tool_call("password-generator", "error", duration, {"error": str(e)})

        return f"""
        <div class="bg-red-500/10 border border-red-500/50 rounded-xl p-4 animate-fade-in">
            <h3 class="text-red-500 font-bold mb-1">Hata</h3>
            <p class="text-red-300 text-sm">{str(e)}</p>
        </div>
        """
