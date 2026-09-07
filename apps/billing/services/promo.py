"""Применение промокода к сумме заказа."""
from decimal import Decimal

from apps.billing.models import PromoCode


class PromoCodeError(Exception):
    pass


def apply_promo_code(code: str, amount: Decimal) -> tuple[Decimal, PromoCode]:
    """
    Проверяет промокод и возвращает (итоговую_сумму, объект_PromoCode).
    Не инкрементирует used_count — это делает вызывающий код после
    успешного создания платежа (см. views.py), чтобы избежать двойного счёта
    при повторных попытках.
    """
    try:
        promo = PromoCode.objects.get(code__iexact=code)
    except PromoCode.DoesNotExist:
        raise PromoCodeError("Промокод не найден.")

    if not promo.is_valid_now:
        raise PromoCodeError("Промокод недействителен или срок его действия истёк.")

    return promo.apply_discount(amount), promo
