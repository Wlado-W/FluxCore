"""
resellers app — реселлерская система поверх User.role/parent_reseller/balance
(см. apps/accounts/models.py).

Реселлер (User.role == RESELLER) создаёт своих субклиентов
(User.role == CLIENT, parent_reseller = реселлер). Когда субклиент
оплачивает тариф, реселлер получает комиссию на свой баланс — фиксируется
в ResellerCommission (аналогично ReferralReward, но по иерархии
реселлер→субклиент, а не по реферальному коду).
"""
from django.conf import settings
from django.db import models


class ResellerProfile(models.Model):
    """Доп. настройки реселлера — размер комиссии, статус одобрения."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reseller_profile"
    )
    commission_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=15,
        help_text="Процент от суммы оплаты субклиента, начисляемый реселлеру",
    )
    is_approved = models.BooleanField(
        default=False, help_text="Реселлер активен только после одобрения администратором"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Реселлер: {self.user.username} ({self.commission_percent}%)"


class ResellerCommission(models.Model):
    """Начисление реселлеру за оплату, совершённую его субклиентом."""
    reseller = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reseller_commissions"
    )
    payment = models.ForeignKey("billing.Payment", on_delete=models.CASCADE, related_name="reseller_commissions")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("reseller", "payment")]  # защита от повторного начисления за один платёж
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.reseller.username}: +{self.amount} (платёж #{self.payment_id})"
