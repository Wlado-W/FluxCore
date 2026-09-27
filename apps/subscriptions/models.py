"""
subscriptions app — models.
"""
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.clients.models import Client



class Subscription(models.Model):
    """Ссылка-подписка клиента — выдаёт список конфигов в нужном формате."""

    class Format(models.TextChoices):
        HAPP = "happ", "Happ"
        V2RAYNG = "v2rayng", "v2rayNG"
        CLASH = "clash", "Clash"
        SING_BOX = "sing-box", "sing-box"
        RAW = "raw", "Сырые ссылки (vless://, vmess:// и т.п.)"

    client = models.OneToOneField(Client, on_delete=models.CASCADE, related_name="subscription")
    token = models.CharField(max_length=64, default=uuid.uuid4, unique=True)
    default_format = models.CharField(max_length=16, choices=Format.choices, default=Format.HAPP)

    auto_select_best_server = models.BooleanField(default=False, help_text="Сортировка по пингу на клиенте")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Sub({self.client.name})"
