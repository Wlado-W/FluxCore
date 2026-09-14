"""
licensing app — активированная лицензия self-hosted инсталляции панели.

License хранит исходный лицензионный ключ (введённый один раз).
RemoteActivationToken хранит короткоживущий токен, полученный от
сервера лицензий продавца — именно он реально決ает, работает панель
или нет (см. apps/licensing/middleware.py).
"""
from django.db import models
from django.utils import timezone

class License(models.Model):
    key = models.TextField(help_text="Лицензионный ключ, введённый администратором")
    customer_name = models.CharField(max_length=255, blank=True)
    activated_at = models.DateTimeField(auto_now_add=True)
    max_nodes = models.IntegerField(default=1)
    expires_at = models.DateTimeField(null=True, blank=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    # Динамическое свойство is_valid
    @property
    def is_valid(self):
        if self.expires_at and self.expires_at < timezone.now():
            return False
        return True

    class Meta:
        ordering = ["-activated_at"]

    def __str__(self):
        return f"Лицензия {self.customer_name or self.key[:16]}"


class RemoteActivationToken(models.Model):
    """
    Короткоживущий токен от сервера лицензий продавца. Обновляется
    периодической задачей Celery (см. apps/licensing/tasks.py). Если этой
    записи нет или она просрочена — LicenseEnforcementMiddleware блокирует
    всю панель.
    """
    token = models.TextField()
    max_nodes = models.PositiveIntegerField(null=True, blank=True)
    issued_at = models.DateTimeField(auto_now_add=True, verbose_name="Дата выдачи")
    expires_at = models.DateTimeField()
    fetched_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-fetched_at"]

    def __str__(self):
        return f"Токен активации (истекает {self.expires_at})"
