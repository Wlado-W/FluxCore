"""
outbounds app — models.

Outbound описывает, куда узел (Node) отправляет трафик дальше:
- напрямую в интернет (freedom)
- в чёрную дыру (blackhole, для блокировок)
- на другой узел цепочки (для каскадирования — chain через RoutingRule)
- через прокси-исходящий (для обхода блокировок между нодами)
"""
import uuid

from django.db import models

from apps.core.models import Node


class Outbound(models.Model):
    """Исходящее соединение, настроенное на конкретной ноде."""

    class Protocol(models.TextChoices):
        FREEDOM = "freedom", "Freedom (прямой выход)"
        BLACKHOLE = "blackhole", "Blackhole (блокировка)"
        VLESS = "vless", "VLESS"
        VMESS = "vmess", "VMess"
        TROJAN = "trojan", "Trojan"
        SHADOWSOCKS = "shadowsocks", "Shadowsocks"
        WIREGUARD = "wireguard", "WireGuard"
        HTTP = "http", "HTTP"
        SOCKS = "socks", "SOCKS"

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="outbounds")
    engine = models.CharField(max_length=16, choices=Node.Engine.choices, default=Node.Engine.XRAY)

    tag = models.CharField(max_length=100, help_text="Уникальный tag outbound'а в конфиге движка")
    protocol = models.CharField(max_length=20, choices=Protocol.choices, default=Protocol.FREEDOM)

    # Для outbound'ов, ведущих на другую ноду (каскад / chain)
    target_node = models.ForeignKey(
        Node, on_delete=models.SET_NULL, null=True, blank=True, related_name="incoming_outbounds",
        help_text="Если задано — этот outbound соединяется со следующей нодой в цепочке",
    )
    target_inbound_tag = models.CharField(
        max_length=100, blank=True,
        help_text="Tag inbound'а на целевой ноде, к которому подключаемся",
    )

    settings = models.JSONField(default=dict, blank=True, help_text="servers, address, port, credentials и т.п.")

    stream_settings = models.JSONField(default=dict, blank=True, help_text="TLS/Reality/transport для исходящего")
    sockopt = models.JSONField(default=dict, blank=True)

    # Балансировка/failover: несколько outbound'ов могут быть объединены в один balancer-тег
    balancer_tag = models.CharField(
        max_length=100, blank=True,
        help_text="Если задано — outbound входит в группу балансировки/failover с этим тегом",
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = [("node", "tag")]
        ordering = ["node", "tag"]

    def __str__(self):
        return f"{self.tag} [{self.protocol}] @ {self.node.name}"
