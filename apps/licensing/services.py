"""
Сервисные функции лицензирования: активация ключа, получение текущей
активной лицензии, проверка лимита нод.
"""
import os
from datetime import datetime

from django.utils import timezone

from .crypto import LicenseSignatureError, verify_license
from .models import License


class LicenseError(Exception):
    pass


class LicenseLimitExceeded(LicenseError):
    pass


def _get_public_key() -> str:
    key = os.environ.get("LICENSING_PUBLIC_KEY")
    if not key:
        raise LicenseError("LICENSING_PUBLIC_KEY не задан в .env — панель не может проверять лицензии.")
    return key


def activate_license(license_key: str) -> License:
    """Проверяет подпись ключа и сохраняет его как активную лицензию."""
    public_key = _get_public_key()

    try:
        payload = verify_license(license_key, public_key)
    except LicenseSignatureError as exc:
        raise LicenseError(str(exc)) from exc

    expires_at = None
    if payload.get("expires_at"):
        expires_at = datetime.fromisoformat(payload["expires_at"])
        if timezone.is_naive(expires_at):
            expires_at = timezone.make_aware(expires_at)

    issued_at = None
    if payload.get("issued_at"):
        issued_at = datetime.fromisoformat(payload["issued_at"])
        if timezone.is_naive(issued_at):
            issued_at = timezone.make_aware(issued_at)

    is_valid = expires_at is None or expires_at > timezone.now()

    # Деактивируем предыдущие лицензии — активна только последняя
    License.objects.update(is_valid=False)

    return License.objects.create(
        key=license_key,
        customer_name=payload.get("customer", ""),
        max_nodes=payload.get("max_nodes"),
        issued_at=issued_at,
        expires_at=expires_at,
        is_valid=is_valid,
    )


def get_active_license() -> License | None:
    return License.objects.filter(is_valid=True).order_by("-activated_at").first()


def revalidate_active_license() -> License | None:
    """
    Периодически (или при каждом критичном действии) перепроверяет срок
    действия текущей лицензии — на случай истечения времени без переактивации.
    """
    license_obj = License.objects.order_by("-activated_at").first()
    if license_obj is None:
        return None

    is_valid = license_obj.expires_at is None or license_obj.expires_at > timezone.now()
    if is_valid != license_obj.is_valid:
        license_obj.is_valid = is_valid
        license_obj.save(update_fields=["is_valid", "last_checked_at"])
    else:
        license_obj.save(update_fields=["last_checked_at"])

    return license_obj


def check_node_limit(current_node_count: int) -> None:
    """Бросает LicenseLimitExceeded, если создание ещё одной ноды превысит лимит лицензии."""
    license_obj = get_active_license()

    if license_obj is None:
        raise LicenseLimitExceeded(
            "Нет действующей лицензии. Активируй лицензионный ключ в /admin/licensing/license/."
        )

    if license_obj.max_nodes is not None and current_node_count >= license_obj.max_nodes:
        raise LicenseLimitExceeded(
            f"Достигнут лимит нод по лицензии ({license_obj.max_nodes}). "
            "Обратись к продавцу для расширения лицензии."
        )
