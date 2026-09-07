"""
Сборка контента подписки в разных форматах (raw, base64 для Happ/v2rayNG,
Clash YAML, sing-box JSON) для конкретного клиента.
"""
import base64

from .link_builder import build_link_for_inbound, build_wireguard_config


def _client_inbounds(client):
    """Все активные inbound'ы, доступные клиенту через его группу."""
    return client.group.inbounds.filter(is_active=True).select_related("node")


def get_client_links(client) -> list[str]:
    """Список всех ссылок клиента (по одной на каждый совместимый inbound)."""
    links = []
    for inbound in _client_inbounds(client):
        if inbound.protocol == "wireguard":
            continue  # WireGuard отдаётся отдельным .conf, не как ссылка
        link = build_link_for_inbound(client, inbound)
        if link:
            links.append(link)
    return links


def build_raw_subscription(client) -> str:
    """Простой список ссылок, по одной на строку."""
    return "\n".join(get_client_links(client))


def build_base64_subscription(client) -> str:
    """
    Стандартный формат для Happ / v2rayNG / большинства мобильных клиентов:
    список ссылок, объединённый переносами строк и закодированный в base64.
    """
    raw = build_raw_subscription(client)
    return base64.b64encode(raw.encode()).decode()


def build_clash_subscription(client) -> str:
    """
    Минимальный Clash-совместимый YAML с proxies для протоколов, которые
    Clash(Meta) понимает нативно (vless/trojan/shadowsocks/hysteria2).
    """
    proxies = []
    for inbound in _client_inbounds(client):
        node = inbound.node
        if inbound.protocol == "vless":
            proxies.append({
                "name": f"{node.name}-{client.name}",
                "type": "vless",
                "server": node.address,
                "port": inbound.port,
                "uuid": str(client.uuid),
                "network": inbound.transport,
                "tls": inbound.security in ("tls", "reality"),
            })
        elif inbound.protocol == "trojan":
            proxies.append({
                "name": f"{node.name}-{client.name}",
                "type": "trojan",
                "server": node.address,
                "port": inbound.port,
                "password": client.password,
            })
        elif inbound.protocol == "shadowsocks":
            proxies.append({
                "name": f"{node.name}-{client.name}",
                "type": "ss",
                "server": node.address,
                "port": inbound.port,
                "cipher": (inbound.transport_settings or {}).get("method", "chacha20-ietf-poly1305"),
                "password": client.password,
            })
        elif inbound.protocol == "hysteria2":
            proxies.append({
                "name": f"{node.name}-{client.name}",
                "type": "hysteria2",
                "server": node.address,
                "port": inbound.port,
                "password": client.password,
            })

    lines = ["proxies:"]
    for p in proxies:
        lines.append(f"  - {p!r}")
    # Простой YAML без внешней зависимости на PyYAML — для MVP этого достаточно,
    # т.к. структура плоская. Позже стоит заменить на yaml.safe_dump.
    return "\n".join(lines)


def get_subscription_content(client, fmt: str) -> tuple[str, str]:
    """
    Возвращает (content, content_type) для заданного формата подписки.
    fmt соответствует Subscription.Format (happ/v2rayng/clash/sing-box/raw).
    """
    if fmt in ("happ", "v2rayng"):
        return build_base64_subscription(client), "text/plain"
    if fmt == "clash":
        return build_clash_subscription(client), "text/yaml"
    if fmt == "raw":
        return build_raw_subscription(client), "text/plain"
    if fmt == "sing-box":
        # TODO: собрать полноценный sing-box outbounds JSON для клиента
        return build_raw_subscription(client), "text/plain"
    raise ValueError(f"Неизвестный формат подписки: {fmt}")
