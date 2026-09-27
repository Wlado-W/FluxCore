"""
Общая логика для раздела «О программе» (ТЗ блок 6) — переиспользуется и
DRF-эндпоинтом (apps.core.api.views.AboutSystemView), и страницей дашборда
(apps.core.views.about_view), чтобы не дублировать один и тот же код.
"""
from django.conf import settings

from apps.licensing.models import License, RemoteActivationToken
from apps.licensing.tiers import get_current_license_tier


def get_about_info() -> dict:
    license_obj = License.objects.first()
    token = RemoteActivationToken.objects.order_by("-fetched_at").first()

    return {
        "app_name": "FluxCore Orchestration Panel",
        "version": getattr(settings, "FLUXCORE_VERSION", "1.0.0"),
        "license": {
            "status": "Active" if (license_obj and license_obj.is_valid) else "Inactive",
            "customer": license_obj.customer_name if license_obj else None,
            "tier": get_current_license_tier().upper(),
            "expires_at": license_obj.expires_at if license_obj else None,
        },
        "system_status": {
            "max_nodes": getattr(token, "max_nodes", 2) if token else 2,
        },
        "eula_url": "/api/v1/system/eula/",
    }
