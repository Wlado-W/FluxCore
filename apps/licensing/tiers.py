from enum import Enum
from functools import wraps
from rest_framework.exceptions import PermissionDenied, ValidationError
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
    return LicenseTier(token.tier.lower())

def check_tier_access(required_tier: LicenseTier) -> bool:
    current_tier = get_current_license_tier()
    return TIER_HIERARCHY.get(current_tier, 1) >= TIER_HIERARCHY.get(required_tier, 1)

def validate_node_limit_for_tier(current_nodes_count: int):
    """
    Проверяет, не превышен ли лимит нод для текущего тарифа.
    Бросает ValidationError, если лимит исчерпан.
    """
    tier = get_current_license_tier()
    
    if tier == LicenseTier.LITE:
        token = RemoteActivationToken.objects.order_by("-fetched_at").first()
        # Лимит из токена или дефолтные 2 ноды для Lite
        max_nodes = getattr(token, "max_nodes", 2) or 2
        
        if current_nodes_count >= max_nodes:
            raise ValidationError(
                f"На тарифе LITE разрешено максимум {max_nodes} нод(ы). "
                f"Для добавления новых серверов обновите лицензию до Premium или Corporate."
            )

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
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not check_tier_access(tier):
                raise PermissionDenied(f"Операция требует лицензию уровня {tier.upper()}.")
            return view_func(request, *args, **kwargs)
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
