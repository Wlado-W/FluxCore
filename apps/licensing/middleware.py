from django.shortcuts import redirect
from django.urls import reverse, resolve, Resolver404
from .services import has_valid_remote_token

_ALLOWED_VIEW_NAMES = {
    "licensing:status",
    "licensing:activate",
    "accounts:login",
    "accounts:logout",
    "admin:login",
}

class LicenseEnforcementMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        
        # Разрешаем статику и медиа
        if path.startswith("/static/") or path.startswith("/media/"):
            return self.get_response(request)

        # Безопасная проверка по названию view
        try:
            resolved = resolve(path)
            if resolved.view_name in _ALLOWED_VIEW_NAMES:
                return self.get_response(request)
        except Resolver404:
            pass

        # Проверка лицензии
        if not has_valid_remote_token():
            return redirect(reverse("licensing:status"))

        return self.get_response(request)
