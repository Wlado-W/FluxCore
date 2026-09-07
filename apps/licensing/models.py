"""
licensing app — активированная лицензия self-hosted инсталляции панели.

Обычно одна запись на инсталляцию (не многопользовательская сущность —
это лицензия самой панели, а не пользователя).
"""
from django.db import models


class License(models.Model):
    key = models.TextField(help_text="Полный лицензионный ключ (payload + подпись)")

    customer_name = models.CharField(max_length=255, blank=True)
    max_nodes = models.PositiveIntegerField(null=True, blank=True, help_text="null = без ограничения")
    issued_at = models.DateTimeField(null=True, blank=True)
    expires_at = models.DateTimeField(null=True, blank=True, help_text="null = бессрочная")

    is_valid = models.BooleanField(default=False, help_text="Результат последней проверки подписи/срока")
    last_checked_at = models.DateTimeField(auto_now=True)
    activated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-activated_at"]

    def __str__(self):
        status = "действительна" if self.is_valid else "недействительна"
        return f"Лицензия {self.customer_name or '—'} ({status})"
