"""
routing app — models.

RoutingRule описывает правила маршрутизации трафика на ноде: по каким
условиям (домен, IP, geosite/geoip, порт, протокол) трафик направляется
в конкретный outbound (или balancer-группу outbound'ов).
"""
from django.db import models

from apps.core.models import Node
from apps.outbounds.models import Outbound


class RoutingRule(models.Model):
    """Правило маршрутизации на конкретной ноде."""

    class MatchType(models.TextChoices):
        DOMAIN = "domain", "Домен"
        IP = "ip", "IP/CIDR"
        GEOSITE = "geosite", "Geosite"
        GEOIP = "geoip", "GeoIP"
        PROTOCOL = "protocol", "Протокол (http/tls/quic/bittorrent)"
        PORT = "port", "Порт"
        SOURCE_PORT = "source_port", "Исходный порт"
        NETWORK = "network", "Сеть (tcp/udp)"
        INBOUND_TAG = "inbound_tag", "Тег inbound'а-источника"

    node = models.ForeignKey(Node, on_delete=models.CASCADE, related_name="routing_rules")

    name = models.CharField(max_length=100, help_text="Понятное имя правила для админки")
    priority = models.PositiveIntegerField(default=100, help_text="Меньше — выше приоритет (проверяется раньше)")

    match_type = models.CharField(max_length=20, choices=MatchType.choices)
    match_values = models.JSONField(
        default=list,
        help_text='Список значений для условия, напр. ["geosite:netflix", "geosite:google"]',
    )

    # Правило либо ведёт в конкретный outbound, либо в balancer-группу (см. Outbound.balancer_tag)
    target_outbound = models.ForeignKey(
        Outbound, on_delete=models.SET_NULL, null=True, blank=True, related_name="routing_rules"
    )
    target_balancer_tag = models.CharField(max_length=100, blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["node", "priority"]
        unique_together = [("node", "name")]

    def __str__(self):
        return f"{self.name} @ {self.node.name} (prio {self.priority})"

    def clean(self):
        from django.core.exceptions import ValidationError
        if not self.target_outbound and not self.target_balancer_tag:
            raise ValidationError("Нужно указать либо target_outbound, либо target_balancer_tag.")
