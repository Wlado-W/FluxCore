"""
Сборка списка пользователей (clients) для конкретного inbound'а — в формате,
который ожидает Xray-core или sing-box для соответствующего протокола.

Один Client может обслуживаться сразу несколькими inbound'ами через
ClientGroup.inbounds (M2M) — этот модуль возвращает только тех клиентов,
которые относятся к переданному inbound'у, и уже отфильтрованы по
активности/сроку/лимиту трафика.
"""
from django.db.models import Q
from django.utils import timezone

from apps.clients.models import Client


def _eligible_clients_for_inbound(inbound):
    """Активные, не истёкшие и не превысившие лимит клиенты для этого inbound'а."""
    now = timezone.now()
    qs = Client.objects.filter(
        group__inbounds=inbound,
        is_active=True,
    ).filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    # Фильтр по лимиту трафика делаем в Python, т.к. сравнение двух полей
    # одной модели неудобно выражать в queryset без F()-выражений с null-логикой.
    return [c for c in qs if not c.is_over_limit]


# ---------------------------------------------------------------------------
# Xray-core
# ---------------------------------------------------------------------------

def build_xray_users(inbound) -> list[dict]:
    """Возвращает список объектов settings.clients[] для Xray-core inbound'а."""
    clients = _eligible_clients_for_inbound(inbound)
    protocol = inbound.protocol

    if protocol == "vless":
        return [
            {"id": str(c.uuid), "email": c.name, "flow": inbound.transport_settings.get("flow", "")}
            for c in clients
        ]

    if protocol == "vmess":
        return [{"id": str(c.uuid), "email": c.name} for c in clients]

    if protocol == "trojan":
        return [{"password": c.password, "email": c.name} for c in clients]

    if protocol == "shadowsocks":
        return [
            {"password": c.password, "email": c.name, "method": inbound.transport_settings.get("method", "")}
            for c in clients
        ]

    if protocol == "mtproto":
        return [{"secret": c.password, "email": c.name} for c in clients]

    # Для протоколов без per-user списка в settings (mixed, http, tun, tunnel,
    # wireguard peers и т.п.) — возвращаем пусто, конфигурация идёт иначе.
    return []


# ---------------------------------------------------------------------------
# sing-box
# ---------------------------------------------------------------------------

def build_singbox_users(inbound) -> list[dict]:
    """Возвращает список объектов users[] для inbound'а sing-box."""
    clients = _eligible_clients_for_inbound(inbound)
    protocol = inbound.protocol

    if protocol in ("vless", "vmess"):
        return [{"uuid": str(c.uuid), "name": c.name} for c in clients]

    if protocol in ("trojan", "shadowsocks", "tuic", "anytls"):
        return [{"password": c.password, "name": c.name} for c in clients]

    if protocol == "shadowtls":
        return [{"password": c.password, "name": c.name} for c in clients]

    if protocol == "naiveproxy":
        return [{"username": c.name, "password": c.password} for c in clients]

    return []
