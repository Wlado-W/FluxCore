"""
inbounds app — models.
"""
import uuid

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

from apps.core.models import Node



class Inbound(models.Model):
    """Входящее соединение на конкретной ноде."""

    class Protocol(models.TextChoices):
        VLESS = "vless", "VLESS"
        VMESS = "vmess", "VMess"
        TROJAN = "trojan", "Trojan"
        SHADOWSOCKS = "shadowsocks", "Shadowsocks"
        WIREGUARD = "wireguard", "WireGuard"
        MTPROTO = "mtproto", "MTProto"
        HYSTERIA2 = "hysteria2", "Hysteria2"
        HYSTERIA = "hysteria", "Hysteria"
        TUIC = "tuic", "TUIC"
        ANYTLS = "anytls", "AnyTLS"
        SHADOWTLS = "shadowtls", "ShadowTLS"
        NAIVEPROXY = "naiveproxy", "NaiveProxy"
        MIXED = "mixed", "Mixed"
        HTTP = "http", "HTTP"
        TUN = "tun", "Tun"
        TUNNEL = "tunnel", "Tunnel"

    class Transport(models.TextChoices):
        RAW = "raw", "Raw (TCP)"
        XHTTP = "xhttp", "XHTTP"
        HTTPUPGRADE = "httpupgrade", "HTTPUpgrade"
        GRPC = "grpc", "gRPC"
        WEBSOCKET = "ws", "WebSocket"
        MKCP = "mkcp", "mKCP"

    class SecurityType(models.TextChoices):
        NONE = "none", "Нет"
        TLS = "tls", "TLS"
        REALITY = "reality", "Reality"

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="inbounds")
    engine = models.CharField(max_length=16, choices=Node.Engine.choices, default=Node.Engine.XRAY)

    tag = models.CharField(max_length=100, help_text="Уникальный tag inbound'а в конфиге движка")
    protocol = models.CharField(max_length=20, choices=Protocol.choices)
    listen = models.CharField(max_length=64, default="0.0.0.0")
    port = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(65535)])

    transport = models.CharField(max_length=16, choices=Transport.choices, default=Transport.RAW)
    transport_settings = models.JSONField(default=dict, blank=True, help_text="path, host, service_name и т.п.")

    security = models.CharField(max_length=16, choices=SecurityType.choices, default=SecurityType.NONE)
    security_settings = models.JSONField(
        default=dict, blank=True,
        help_text="Для TLS: сертификаты/ключи. Для Reality: dest, private_key, short_ids, server_names",
    )

    sniffing_enabled = models.BooleanField(default=True)
    sniffing_dest_override = models.JSONField(default=list, blank=True, help_text='["http", "tls", "quic"]')

    tcp_mask_enabled = models.BooleanField(default=False)
    tcp_mask_settings = models.JSONField(default=dict, blank=True)

    sockopt = models.JSONField(default=dict, blank=True, help_text="tcpFastOpen, mark, tproxy и т.п.")
    proxy_protocol_enabled = models.BooleanField(default=False)
    http_obfuscation_settings = models.JSONField(default=dict, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("node", "port")]
        ordering = ["node", "port"]

    def __str__(self):
        return f"{self.tag} [{self.protocol}] @ {self.node.name}:{self.port}"

