"""
audit app — модель журнала действий администраторов.

Логируются: создание/изменение/удаление ключевых объектов (Node, Inbound,
Outbound, RoutingRule, Client, ClientGroup), а также вход/выход/неудачные
попытки входа (через сигналы django.contrib.auth).
"""
from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    class Action(models.TextChoices):
        CREATED = "created", "Создание"
        UPDATED = "updated", "Изменение"
        DELETED = "deleted", "Удаление"
        LOGIN = "login", "Вход"
        LOGOUT = "logout", "Выход"
        LOGIN_FAILED = "login_failed", "Неудачная попытка входа"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="audit_logs",
        help_text="Кто совершил действие (null — если система или неаутентифицированный запрос)",
    )
    action = models.CharField(max_length=20, choices=Action.choices)

    model_name = models.CharField(max_length=100, blank=True, help_text="Например: core.Node")
    object_id = models.CharField(max_length=100, blank=True)
    object_repr = models.CharField(max_length=255, blank=True, help_text="Человекочитаемое представление объекта")

    changes = models.JSONField(default=dict, blank=True, help_text="Изменённые поля: {field: [old, new]}")
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_name", "object_id"]),
            models.Index(fields=["actor", "created_at"]),
        ]

    def __str__(self):
        actor_label = self.actor.username if self.actor else "система"
        return f"{actor_label}: {self.get_action_display()} {self.object_repr or self.model_name}"
