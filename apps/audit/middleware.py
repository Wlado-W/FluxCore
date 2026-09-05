"""
Middleware, кладущий текущего пользователя и IP в contextvar перед
обработкой запроса — чтобы сигналы моделей (post_save/post_delete) знали,
кто выполняет действие (см. apps/audit/context.py и signals.py).
"""
from .context import clear_current_request_context, set_current_request_context


def _get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class AuditLogMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        set_current_request_context(getattr(request, "user", None), _get_client_ip(request))
        try:
            response = self.get_response(request)
        finally:
            clear_current_request_context()
        return response
