"""
Middleware, блокирующая доступ ко ВСЕЙ панели (не к одной кнопке "создать
ноду"), если нет действующего, не просроченного токена активации от
сервера лицензий продавца.

Это ключевое архитектурное отличие от прежней схемы: раньше проверка
лицензии была спрятана в одном месте кода (легко удалить правкой файла).
Теперь это middleware, применяемая глобально на каждый запрос — чтобы
обойти её, нужно найти и вырезать именно эту строку в MIDDLEWARE
настроек, что технически возможно (это Python, полный обход в
self-hosted софте невозможен принципиально), но требует явного и
осознанного взлома, а не одной случайно найденной галочки.

Реальная сила защиты — в том, что даже вырезав middleware, панель
всё равно не получит СВЕЖИЙ токен без доступа к серверу лицензий
продавца, а старые токены истекают за 24 часа.
"""
from django.shortcuts import redirect
from django.urls import reverse

from .services import has_valid_remote_token

# Пути, доступные всегда — иначе невозможно будет даже открыть страницу
# активации или войти в систему, чтобы её открыть.
_ALLOWED_PREFIXES = ("/license/", "/accounts/login/", "/accounts/logout/", "/static/", "/admin/login/")


class LicenseEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if any(request.path.startswith(prefix) for prefix in _ALLOWED_PREFIXES):
            return self.get_response(request)

        if not has_valid_remote_token():
            return redirect(reverse("licensing:status"))

        return self.get_response(request)
