"""
telegram_bot app — привязка Telegram-аккаунта к пользователю панели.

Флоу привязки:
1. Пользователь на сайте нажимает «Привязать Telegram» → создаётся
   TelegramLinkCode с коротким кодом и сроком жизни 10 минут.
2. Пользователь отправляет боту команду /link <код>.
3. Бот находит TelegramLinkCode по коду, создаёт TelegramAccount,
   помечает код использованным.
"""
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import models
from django.utils import timezone


def generate_link_code() -> str:
    return uuid.uuid4().hex[:8].upper()


def default_link_code_expiry():
    return timezone.now() + timedelta(minutes=10)


class TelegramAccount(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="telegram_account"
    )
    telegram_id = models.BigIntegerField(unique=True)
    telegram_username = models.CharField(max_length=100, blank=True)
    linked_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} ↔ @{self.telegram_username or self.telegram_id}"


class TelegramLinkCode(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="telegram_link_codes"
    )
    code = models.CharField(max_length=16, unique=True, default=generate_link_code)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=default_link_code_expiry)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.code} ({self.user.username})"

    @property
    def is_valid(self) -> bool:
        return not self.is_used and self.expires_at > timezone.now()
