"""
Context processor, добавляющий активную тему в контекст каждого шаблона,
чтобы base.html мог отрендерить переопределение CSS-переменных.
"""
from apps.licensing.tiers import LicenseTier, get_current_license_tier

from .models import SystemBranding, Theme


def active_theme(request):
    theme = Theme.objects.filter(is_active=True).first()
    return {"active_theme": theme}


def branding(request):
    """
    White Label (только Corporate, см. ТЗ блок 3): если тариф ниже
    Corporate — всегда отдаём дефолтный бренд FluxCore, никакого upload'а
    из SystemBranding, даже если он ранее был сохранён (например, лицензию
    понизили с Corporate до Premium — кастомный бренд должен исчезнуть,
    а не продолжать работать "по инерции").
    """
    if get_current_license_tier() != LicenseTier.CORPORATE:
        return {
            "branding": {
                "app_name": "FluxCore",
                "logo_url": None,
                "favicon_url": None,
                "custom_css": "",
            }
        }

    system_branding = SystemBranding.load()
    return {
        "branding": {
            "app_name": system_branding.app_name or "FluxCore",
            "logo_url": system_branding.logo.url if system_branding.logo else None,
            "favicon_url": system_branding.favicon.url if system_branding.favicon else None,
            "custom_css": system_branding.custom_css,
        }
    }
