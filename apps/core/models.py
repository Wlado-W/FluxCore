"""
core app — models.
"""
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class NodeGroup(models.Model):
    """Группа нод — например, для каскадирования (chain) или гео-региона."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    is_cascade = models.BooleanField(
        default=False,
        help_text="Если True — ноды в этой группе связаны цепочкой (chain outbound → inbound следующей ноды)",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Node(models.Model):
    """Сервер (нода), на котором работает агент + Xray и/или sing-box."""

    class Engine(models.TextChoices):
        XRAY = "xray", "Xray-core"
        SING_BOX = "sing-box", "sing-box"

    class Status(models.TextChoices):
        PENDING = "pending", "Ожидает установки"
        ONLINE = "online", "Онлайн"
        OFFLINE = "offline", "Оффлайн"
        ERROR = "error", "Ошибка"

    name = models.CharField(max_length=100)
    group = models.ForeignKey(
        NodeGroup, on_delete=models.SET_NULL, null=True, blank=True, related_name="nodes"
    )

    address = models.CharField(max_length=255, help_text="IP или домен ноды")
    port_agent = models.PositiveIntegerField(default=62050, help_text="Порт агента на ноде")
    port_api = models.PositiveIntegerField(default=62051, help_text="Порт gRPC/API движка")

    # Какие движки установлены/включены на этой ноде.
    # Нода может уметь и Xray, и sing-box одновременно — используем M2M-подобный подход через JSON.
    engines_enabled = models.JSONField(
        default=list,
        help_text='Список активных движков, напр. ["xray", "sing-box"]',
    )

    agent_token = models.CharField(
        max_length=128, default=uuid.uuid4, unique=True,
        help_text="Токен для аутентификации агента ноды перед панелью",
    )

    country_code = models.CharField(max_length=2, blank=True, help_text="ISO 3166-1 alpha-2, для гео на карте")
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)

    status = models.CharField(max_length=16, choices=Status.choices, default=Status.PENDING)
    last_seen_at = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True, help_text="Выключить ноду из работы, не удаляя")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.address})"


class NodeMetric(models.Model):
    """Точки мониторинга — снимки состояния ноды во времени."""
    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="metrics")
    cpu_percent = models.FloatField()
    ram_percent = models.FloatField()
    disk_percent = models.FloatField()
    traffic_up_bytes = models.BigIntegerField(default=0)
    traffic_down_bytes = models.BigIntegerField(default=0)
    uptime_seconds = models.BigIntegerField(default=0)
    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [models.Index(fields=["node", "recorded_at"])]
        ordering = ["-recorded_at"]

