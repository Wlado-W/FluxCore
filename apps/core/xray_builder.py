"""
Сборка конфига Xray-core (config.json) на основе моделей Node, Inbound,
Outbound, RoutingRule для конкретной ноды.

Формат соответствует стандартной схеме Xray-core:
https://xtls.github.io/config/
"""
from apps.clients.services.user_builder import build_wireguard_peers, build_xray_users
from apps.core.models import Node

# Протоколы, у которых пользователи передаются через settings.clients[]
_CLIENTS_KEY_PROTOCOLS = {"vless", "vmess", "trojan", "shadowsocks", "mtproto"}


def _build_stream_settings(inbound) -> dict:
    """Собирает streamSettings для inbound'а: transport + TLS/Reality."""
    stream: dict = {"network": inbound.transport}

    # Transport-специфичные настройки (path, host, serviceName и т.п.)
    transport_key_map = {
        "raw": "rawSettings",
        "xhttp": "xhttpSettings",
        "httpupgrade": "httpupgradeSettings",
        "grpc": "grpcSettings",
        "ws": "wsSettings",
        "mkcp": "kcpSettings",
    }
    settings_key = transport_key_map.get(inbound.transport)
    if settings_key and inbound.transport_settings:
        stream[settings_key] = inbound.transport_settings

    # Безопасность: TLS / Reality
    if inbound.security == "tls":
        stream["security"] = "tls"
        stream["tlsSettings"] = inbound.security_settings
    elif inbound.security == "reality":
        stream["security"] = "reality"
        stream["realitySettings"] = inbound.security_settings
    else:
        stream["security"] = "none"

    if inbound.tcp_mask_enabled and inbound.tcp_mask_settings:
        stream["tcpSettings"] = {**stream.get("tcpSettings", {}), **inbound.tcp_mask_settings}

    if inbound.sockopt:
        stream["sockopt"] = inbound.sockopt

    return stream


def _build_inbound(inbound) -> dict:
    entry = {
        "tag": inbound.tag,
        "listen": inbound.listen,
        "port": inbound.port,
        "protocol": inbound.protocol,
        "settings": {},
        "streamSettings": _build_stream_settings(inbound),
    }

    if inbound.protocol in _CLIENTS_KEY_PROTOCOLS:
        entry["settings"]["clients"] = build_xray_users(inbound)

    elif inbound.protocol == "wireguard":
        # WireGuard: секретный ключ ноды берётся из security_settings,
        # peers — список клиентов с публичными ключами.
        entry["settings"] = {
            **inbound.security_settings,
            "peers": build_wireguard_peers(inbound),
        }

    elif inbound.protocol in ("mixed", "http", "tun", "tunnel"):
        # Эти протоколы настраиваются напрямую через transport_settings
        # (например, статичные логин/пароль для http/socks, или интерфейс для tun),
        # без привязки к списку Client — обычно используются как служебные/локальные.
        entry["settings"] = inbound.transport_settings or {}

    if inbound.sniffing_enabled:
        entry["sniffing"] = {
            "enabled": True,
            "destOverride": inbound.sniffing_dest_override or ["http", "tls", "quic"],
        }

    if inbound.proxy_protocol_enabled:
        entry.setdefault("streamSettings", {}).setdefault("sockopt", {})["acceptProxyProtocol"] = True

    if inbound.http_obfuscation_settings:
        entry["httpObfuscation"] = inbound.http_obfuscation_settings

    return entry


def _build_outbound(outbound) -> dict:
    entry = {
        "tag": outbound.tag,
        "protocol": outbound.protocol,
        "settings": outbound.settings or {},
    }

    if outbound.stream_settings:
        entry["streamSettings"] = outbound.stream_settings

    if outbound.sockopt:
        entry.setdefault("streamSettings", {})["sockopt"] = outbound.sockopt

    # Каскадирование: outbound ведёт на inbound следующей ноды
    if outbound.target_node_id and outbound.target_inbound_tag:
        entry["settings"] = {
            **entry["settings"],
            "vnext": entry["settings"].get("vnext", []),
        }
        # Реальный адрес/порт целевой ноды должен быть добавлен в settings
        # на этапе применения (deploy.py), т.к. может меняться (IP ротация и т.п.)

    return entry


def _build_balancers(outbounds) -> list:
    """Группирует outbound'ы с одинаковым balancer_tag в balancer-блоки."""
    tags_by_balancer: dict[str, list[str]] = {}
    for ob in outbounds:
        if ob.balancer_tag:
            tags_by_balancer.setdefault(ob.balancer_tag, []).append(ob.tag)

    return [
        {"tag": balancer_tag, "selector": tags}
        for balancer_tag, tags in tags_by_balancer.items()
    ]


def _build_routing_rule(rule) -> dict:
    entry: dict = {}

    match_key_map = {
        "domain": "domain",
        "ip": "ip",
        "geosite": "domain",   # geosite:xxx передаётся строкой внутри domain[]
        "geoip": "ip",         # geoip:xxx передаётся строкой внутри ip[]
        "port": "port",
        "source_port": "sourcePort",
        "network": "network",
        "inbound_tag": "inboundTag",
    }
    key = match_key_map.get(rule.match_type)
    if key:
        entry[key] = rule.match_values

    if rule.match_type == "protocol":
        entry["protocol"] = rule.match_values

    if rule.target_outbound_id:
        entry["outboundTag"] = rule.target_outbound.tag
    elif rule.target_balancer_tag:
        entry["balancerTag"] = rule.target_balancer_tag

    return entry


def build_xray_config(node: Node) -> dict:
    """Собирает полный config.json для Xray-core на указанной ноде."""
    inbounds = node.inbounds.filter(is_active=True, engine=Node.Engine.XRAY)
    outbounds = node.outbounds.filter(is_active=True, engine=Node.Engine.XRAY)
    routing_rules = node.routing_rules.filter(is_active=True).order_by("priority")

    config = {
        "log": {"loglevel": "warning"},
        "inbounds": [_build_inbound(ib) for ib in inbounds],
        "outbounds": [_build_outbound(ob) for ob in outbounds],
        "routing": {
            "domainStrategy": "AsIs",
            "balancers": _build_balancers(outbounds),
            "rules": [_build_routing_rule(r) for r in routing_rules],
        },
    }

    # Гарантируем наличие freedom/blackhole по умолчанию, если не заданы явно
    existing_tags = {ob["tag"] for ob in config["outbounds"]}
    if "direct" not in existing_tags:
        config["outbounds"].append({"tag": "direct", "protocol": "freedom", "settings": {}})
    if "block" not in existing_tags:
        config["outbounds"].append({"tag": "block", "protocol": "blackhole", "settings": {}})

    return config
