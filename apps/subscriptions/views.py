"""
Публичная выдача подписки по токену: /sub/<token>/
и QR-кода: /sub/<token>/qr/

Формат выбирается так:
1. Явный query-параметр ?format=clash|happ|v2rayng|raw|sing-box, если передан
2. Иначе — Subscription.default_format
"""
from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404

from .models import Subscription
from .services.format_builder import get_subscription_content
from .services.qr import build_subscription_qr_png


def subscription_view(request, token: str) -> HttpResponse:
    subscription = get_object_or_404(Subscription, token=token)
    fmt = request.GET.get("format") or subscription.default_format

    try:
        content, content_type = get_subscription_content(subscription.client, fmt)
    except ValueError as exc:
        raise Http404(str(exc)) from exc

    return HttpResponse(content, content_type=content_type)


def subscription_qr_view(request, token: str) -> HttpResponse:
    subscription = get_object_or_404(Subscription, token=token)
    url = request.build_absolute_uri(f"/sub/{subscription.token}/")
    png_bytes = build_subscription_qr_png(url)
    return HttpResponse(png_bytes, content_type="image/png")
