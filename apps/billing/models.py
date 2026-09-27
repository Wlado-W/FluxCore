"""
billing app — тарифы, промокоды, платежи.

Tariff описывает, что покупает клиент (срок действия и/или лимит трафика).
Payment фиксирует попытку оплаты через внешнего провайдера (см.
apps/billing/services/providers.py) и по завершении продлевает/активирует
Client согласно купленному тарифу.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone


class Tariff(models.Model):
    """Тарифный план — по времени, по трафику, безлимит или комбинированный."""

    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default="RUB")

    duration_days = models.PositiveIntegerField(null=True, blank=True, help_text="null = бессрочно")
    traffic_limit_bytes = models.BigIntegerField(null=True, blank=True, help_text="null = безлимит")
    max_devices = models.PositiveSmallIntegerField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["price"]

    def __str__(self):
        return f"{self.name} — {self.price} {self.currency}"


class PromoCode(models.Model):
    class DiscountType(models.TextChoices):
        PERCENT = "percent", "Процент"
        FIXED = "fixed", "Фиксированная сумма"

    code = models.CharField(max_length=32, unique=True)
    discount_type = models.CharField(max_length=10, choices=DiscountType.choices, default=DiscountType.PERCENT)
    discount_value = models.DecimalField(max_digits=10, decimal_places=2, help_text="Проценты (0-100) или сумма")

    max_uses = models.PositiveIntegerField(null=True, blank=True, help_text="null = без ограничения")
    used_count = models.PositiveIntegerField(default=0)

    valid_from = models.DateTimeField(null=True, blank=True)
    valid_until = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.code

    @property
    def is_valid_now(self) -> bool:
        if not self.is_active:
            return False
        now = timezone.now()
        if self.valid_from and now < self.valid_from:
            return False
        if self.valid_until and now > self.valid_until:
            return False
        if self.max_uses is not None and self.used_count >= self.max_uses:
            return False
        return True

    def apply_discount(self, amount: Decimal) -> Decimal:
        if self.discount_type == self.DiscountType.PERCENT:
            discounted = amount * (Decimal("100") - self.discount_value) / Decimal("100")
        else:
            discounted = amount - self.discount_value
        return max(discounted, Decimal("0"))


class Payment(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает оплаты"
        COMPLETED = "completed", "Оплачен"
        FAILED = "failed", "Ошибка"
        REFUNDED = "refunded", "Возврат"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="payments"
    )
    client = models.ForeignKey(
        "clients.Client", on_delete=models.SET_NULL, null=True, blank=True, related_name="payments",
        help_text="Клиент, которому продлевается доступ (если применимо)",
    )
    tariff = models.ForeignKey(Tariff, on_delete=models.PROTECT, related_name="payments")
    promo_code = models.ForeignKey(
        PromoCode, on_delete=models.SET_NULL, null=True, blank=True, related_name="payments"
    )

    amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Итоговая сумма после скидки")
    currency = models.CharField(max_length=3, default="RUB")

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    provider = models.CharField(max_length=32, blank=True, help_text="Название платёжной системы (yookassa, stripe и т.п.)")
    external_id = models.CharField(max_length=255, blank=True, help_text="ID платежа у провайдера")

    created_at = models.DateTimeField(auto_now_add=True)
    paid_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payment#{self.pk} {self.amount} {self.currency} ({self.status})"
