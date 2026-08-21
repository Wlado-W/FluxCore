"""
Кастомная модель пользователя — нужна для ролей (admin/reseller/client),
2FA, и владения клиентами (Client.owner).
"""
from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        RESELLER = "reseller", "Реселлер"
        CLIENT = "client", "Клиент"

    role = models.CharField(max_length=16, choices=Role.choices, default=Role.CLIENT)
    is_2fa_enabled = models.BooleanField(default=False)
    totp_secret = models.CharField(max_length=64, blank=True)

    # Для реселлерской системы
    balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    parent_reseller = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="sub_accounts"
    )
