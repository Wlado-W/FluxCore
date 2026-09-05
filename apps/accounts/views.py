"""
Логин с опциональной двухфакторной аутентификацией (TOTP) и страница
настройки 2FA для пользователя.

Флоу входа:
1. /accounts/login/  — обычная форма логин/пароль (AuthenticationForm).
   Если у пользователя is_2fa_enabled=False — логиним сразу.
   Если True — НЕ логиним ещё, кладём user.id в session["pre_2fa_user_id"]
   и редиректим на шаг проверки кода.
2. /accounts/login/verify/ — форма с 6-значным кодом. При успехе — реальный
   django.contrib.auth.login() и переход на next (или дашборд).

Настройка 2FA:
- /accounts/2fa/setup/      — показывает QR-код + секрет (текстом на случай,
  если QR не сканируется), просит ввести код для подтверждения включения.
- /accounts/2fa/setup/qr.png — сама картинка QR (PNG).
"""
import io

import qrcode
from django.contrib.auth import login as auth_login
from django.contrib.auth import logout as auth_logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.shortcuts import redirect, render

from .services.totp import generate_totp_secret, get_provisioning_uri, verify_totp_code

User = get_user_model()

PRE_2FA_SESSION_KEY = "pre_2fa_user_id"
PENDING_2FA_SECRET_SESSION_KEY = "pending_2fa_secret"


def login_view(request):
    if request.user.is_authenticated:
        return redirect("dashboard:index")

    if request.method == "POST":
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            if user.is_2fa_enabled:
                request.session[PRE_2FA_SESSION_KEY] = user.id
                next_url = request.POST.get("next") or request.GET.get("next", "")
                return redirect(f"/accounts/login/verify/?next={next_url}")
            auth_login(request, user)
            return redirect(request.POST.get("next") or "dashboard:index")
    else:
        form = AuthenticationForm(request)

    return render(request, "accounts/login.html", {"form": form})


def login_verify_view(request):
    user_id = request.session.get(PRE_2FA_SESSION_KEY)
    if not user_id:
        return redirect("accounts:login")

    error = None
    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            del request.session[PRE_2FA_SESSION_KEY]
            return redirect("accounts:login")

        if verify_totp_code(user.totp_secret, code):
            del request.session[PRE_2FA_SESSION_KEY]
            auth_login(request, user)
            next_url = request.POST.get("next") or "dashboard:index"
            return redirect(next_url)
        error = "Неверный код. Попробуй ещё раз."

    return render(request, "accounts/login_verify.html", {"error": error})


def logout_view(request):
    auth_logout(request)
    return redirect("accounts:login")


@login_required
def setup_2fa_view(request):
    user = request.user

    if request.method == "POST":
        code = request.POST.get("code", "").strip()
        pending_secret = request.session.get(PENDING_2FA_SECRET_SESSION_KEY)
        if pending_secret and verify_totp_code(pending_secret, code):
            user.totp_secret = pending_secret
            user.is_2fa_enabled = True
            user.save(update_fields=["totp_secret", "is_2fa_enabled"])
            del request.session[PENDING_2FA_SECRET_SESSION_KEY]
            return render(request, "accounts/2fa_setup.html", {"enabled": True, "success": True})
        return render(
            request, "accounts/2fa_setup.html",
            {"enabled": user.is_2fa_enabled, "error": "Неверный код, попробуй снова.",
             "secret": pending_secret},
        )

    if user.is_2fa_enabled:
        return render(request, "accounts/2fa_setup.html", {"enabled": True})

    # Генерируем новый секрет только на этапе настройки — он не сохраняется
    # в БД, пока пользователь не подтвердит его правильным кодом.
    secret = generate_totp_secret()
    request.session[PENDING_2FA_SECRET_SESSION_KEY] = secret

    return render(request, "accounts/2fa_setup.html", {"enabled": False, "secret": secret})


@login_required
def setup_2fa_qr_view(request):
    secret = request.session.get(PENDING_2FA_SECRET_SESSION_KEY)
    if not secret:
        return HttpResponse(status=404)

    uri = get_provisioning_uri(request.user, secret)
    img = qrcode.make(uri, box_size=6, border=2)
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return HttpResponse(buf.getvalue(), content_type="image/png")


@login_required
def disable_2fa_view(request):
    if request.method == "POST":
        request.user.is_2fa_enabled = False
        request.user.totp_secret = ""
        request.user.save(update_fields=["is_2fa_enabled", "totp_secret"])
        return redirect("accounts:setup_2fa")
    return render(request, "accounts/2fa_disable_confirm.html")
