"""
clients app — models.
"""
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.inbounds.models import Inbound



class ClientGroup(models.Model):
    """Группа клиентов с общим набором inbound'ов / тарифом."""
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    inbounds = models.ManyToManyField(Inbound, related_name="client_groups", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Client(models.Model):
    """Клиент VPN — подключается через один или несколько inbound'ов группы."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="vpn_clients",
        help_text="Владелец клиента в системе (для реселлерки/ЛК)",
    )
    group = models.ForeignKey(ClientGroup, on_delete=models.PROTECT, related_name="clients")

    name = models.CharField(max_length=100)
    uuid = models.UUIDField(default=uuid.uuid4, unique=True, help_text="Для vless/vmess")
    password = models.CharField(max_length=128, blank=True, help_text="Для trojan/shadowsocks")

    traffic_limit_bytes = models.BigIntegerField(null=True, blank=True, help_text="null = безлимит")
    traffic_used_bytes = models.BigIntegerField(default=0)
    traffic_reset_day = models.PositiveSmallIntegerField(
        null=True, blank=True, help_text="День месяца для авто-сброса трафика (1-28)"
    )

    expires_at = models.DateTimeField(null=True, blank=True, help_text="null = бессрочно")
    max_devices = models.PositiveSmallIntegerField(null=True, blank=True, help_text="null = без ограничений")

    is_active = models.BooleanField(default=True)
    is_trial = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} ({self.owner})"

    @property
    def is_expired(self) -> bool:
        from django.utils import timezone
        return bool(self.expires_at and self.expires_at < timezone.now())

    @property
    def is_over_limit(self) -> bool:
        return bool(self.traffic_limit_bytes and self.traffic_used_bytes >= self.traffic_limit_bytes)

