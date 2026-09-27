from enum import Enum
from functools import wraps
from django.core.exceptions import PermissionDenied
from apps.licensing.models import RemoteActivationToken

class LicenseTier(str, Enum):
    LITE = "lite"
    PREMIUM = "premium"
    CORPORATE = "corporate"

TIER_HIERARCHY = {
    LicenseTier.LITE: 1,
    LicenseTier.PREMIUM: 2,
    LicenseTier.CORPORATE: 3,
}

def get_current_license_tier() -> LicenseTier:
    """Получает текущий тариф панели из токена активации."""
    token = RemoteActivationToken.objects.order_by("-fetched_at").first()
    if not token or not getattr(token, "tier", None):
        return LicenseTier.LITE
    try:
        return LicenseTier(token.tier.lower())
    except ValueError:
        # Неизвестное/повреждённое значение tier — безопасный дефолт, а не 500-я ошибка.
        return LicenseTier.LITE

def check_tier_access(required_tier: LicenseTier) -> bool:
    current_tier = get_current_license_tier()
    return TIER_HIERARCHY.get(current_tier, 1) >= TIER_HIERARCHY.get(required_tier, 1)

# --- DRF Permission Class ---
from rest_framework.permissions import BasePermission

class RequireTierPermission(BasePermission):
    required_tier = LicenseTier.LITE

    def has_permission(self, request, view):
        tier = getattr(view, "required_tier", self.required_tier)
        if not check_tier_access(tier):
            raise PermissionDenied(
                detail=f"Данная функция недоступна на вашем тарифе. Требуется тариф {tier.upper()}."
            )
        return True

# --- Decorator for Views / DRF Actions ---
def require_tier(tier: LicenseTier):
    """
    Работает и как декоратор обычной Django view (request, *args), и как
    декоратор метода DRF APIView/ViewSet (self, request, *args) — сам
    декоратор не трогает конкретные позиционные аргументы, а просто
    прозрачно их прокидывает, поэтому ему всё равно, что идёт первым.
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(*args, **kwargs):
            if not check_tier_access(tier):
                raise PermissionDenied(f"Операция требует лицензию уровня {tier.upper()}.")
            return view_func(*args, **kwargs)
        return _wrapped_view
    return decorator

# --- Django Context Processor for UI Templates ---
def license_context(request):
    tier = get_current_license_tier()
    return {
        "LICENSE_TIER": tier.value,
        "IS_LITE": tier == LicenseTier.LITE,
        "IS_PREMIUM": tier == LicenseTier.PREMIUM,
        "IS_CORPORATE": tier == LicenseTier.CORPORATE,
        "CAN_USE_WHITE_LABEL": tier == LicenseTier.CORPORATE,
        "CAN_USE_CASCADE": tier in [LicenseTier.PREMIUM, LicenseTier.CORPORATE],
    }
