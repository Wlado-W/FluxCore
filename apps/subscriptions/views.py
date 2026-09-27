"""
Публичная выдача подписки по токену: /sub/<token>/
и QR-кода: /sub/<token>/qr/
и deep-link'ов для мобильных приложений: /sub/<token>/apps/
и человекочитаемой HTML-страницы: /sub/<token>/info/
   (страница для открытия в браузере — с QR и кнопками "открыть в приложении";
   именно сюда, а не в сырой конфиг, вставляется рекламный блок Corporate —
   см. ТЗ блок 3 "White Labeling, Реклама и Брендинг")

Формат выбирается так:
1. Явный query-параметр ?format=clash|happ|v2rayng|raw|sing-box, если передан
2. Иначе — Subscription.default_format
"""
from django.http import Http404, HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render

from apps.licensing.tiers import LicenseTier, get_current_license_tier
from apps.panel_settings.models import SystemBranding

from .models import Subscription
from .services.deep_links import build_deep_links
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


def subscription_deep_links_view(request, token: str) -> JsonResponse:
    """Возвращает deep-link'и для одного тапа импорта в мобильные приложения."""
    subscription = get_object_or_404(Subscription, token=token)
    url = request.build_absolute_uri(f"/sub/{subscription.token}/")
    return JsonResponse(build_deep_links(url))


def subscription_info_view(request, token: str) -> HttpResponse:
    """
    Человекочитаемая страница подписки — то, что клиент открывает в браузере
    (а не импортирует напрямую в приложение): QR-код, кнопки быстрого
    импорта и, на тарифе Corporate, управляемый рекламный/информационный
    блок владельца панели (SystemBranding.ad_*).
    """
    subscription = get_object_or_404(Subscription, token=token)
    url = request.build_absolute_uri(f"/sub/{subscription.token}/")

    ad = None
    app_name = "FluxCore"
    if get_current_license_tier() == LicenseTier.CORPORATE:
        system_branding = SystemBranding.load()
        app_name = system_branding.app_name or "FluxCore"
        if system_branding.ad_enabled and (system_branding.ad_title or system_branding.ad_content):
            ad = {
                "title": system_branding.ad_title,
                "content": system_branding.ad_content,
                "link": system_branding.ad_link,
            }

    return render(request, "subscriptions/subscription_info.html", {
        "subscription": subscription,
        "subscription_url": url,
        "deep_links": build_deep_links(url),
        "app_name": app_name,
        "ad": ad,
    })
