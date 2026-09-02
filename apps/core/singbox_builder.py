"""
Сборка конфига sing-box на основе моделей Node, Inbound, Outbound,
RoutingRule для протоколов, которых нет в Xray-core: TUIC, ShadowTLS,
NaiveProxy, AnyTLS (и как альтернативный движок для остальных).

Формат соответствует схеме sing-box:
https://sing-box.sagernet.org/configuration/
"""
from apps.clients.services.user_builder import build_singbox_users, build_wireguard_peers
from apps.core.models import Node

# Протоколы sing-box, которых нет в Xray-core — для них этот билдер обязателен.
SINGBOX_ONLY_PROTOCOLS = {"tuic", "shadowtls", "naiveproxy", "anytls"}

# Протоколы, у которых пользователи передаются через users[]
_USERS_KEY_PROTOCOLS = {"vless", "vmess", "trojan", "shadowsocks", "tuic", "anytls", "shadowtls", "naiveproxy"}


def _build_tls(inbound) -> dict | None:
    if inbound.security == "tls":
        return {"enabled": True, **inbound.security_settings}
    if inbound.security == "reality":
        return {"enabled": True, "reality": {"enabled": True, **inbound.security_settings}}
    return None


def _build_inbound(inbound) -> dict:
    entry = {
        "type": inbound.protocol,
        "tag": inbound.tag,
        "listen": inbound.listen,
        "listen_port": inbound.port,
    }

    tls = _build_tls(inbound)
    if tls:
        entry["tls"] = tls

    if inbound.sniffing_enabled:
        entry["sniff"] = True
        if inbound.sniffing_dest_override:
            entry["sniff_override_destination"] = True

    if inbound.protocol in _USERS_KEY_PROTOCOLS:
        entry["users"] = build_singbox_users(inbound)

    elif inbound.protocol == "wireguard":
        entry.update(inbound.security_settings)
        entry["peers"] = build_wireguard_peers(inbound)

    elif inbound.protocol in ("mixed", "http", "tun", "tunnel"):
        entry.update(inbound.transport_settings or {})

    return entry


def _build_outbound(outbound) -> dict:
    return {
        "type": outbound.protocol,
        "tag": outbound.tag,
        **(outbound.settings or {}),
    }


def _build_route_rule(rule) -> dict:
    entry: dict = {}

    match_key_map = {
        "domain": "domain",
        "ip": "ip_cidr",
        "geosite": "geosite",
        "geoip": "geoip",
        "port": "port",
        "source_port": "source_port",
        "network": "network",
        "inbound_tag": "inbound",
    }
    key = match_key_map.get(rule.match_type)
    if key:
        entry[key] = rule.match_values

    if rule.target_outbound_id:
        entry["outbound"] = rule.target_outbound.tag
    elif rule.target_balancer_tag:
        # sing-box не имеет прямого аналога balancer — ближайший эквивалент
        # это urltest/selector outbound, который нужно создавать отдельно.
        entry["outbound"] = rule.target_balancer_tag

    return entry


def build_singbox_config(node: Node) -> dict:
    """Собирает полный конфиг sing-box для указанной ноды."""
    inbounds = node.inbounds.filter(is_active=True, engine=Node.Engine.SING_BOX)
    outbounds = node.outbounds.filter(is_active=True, engine=Node.Engine.SING_BOX)
    routing_rules = node.routing_rules.filter(is_active=True).order_by("priority")

    config = {
        "log": {"level": "warn"},
        "inbounds": [_build_inbound(ib) for ib in inbounds],
        "outbounds": [_build_outbound(ob) for ob in outbounds],
        "route": {
            "rules": [_build_route_rule(r) for r in routing_rules],
        },
    }

    existing_tags = {ob["tag"] for ob in config["outbounds"]}
    if "direct" not in existing_tags:
        config["outbounds"].append({"type": "direct", "tag": "direct"})
    if "block" not in existing_tags:
        config["outbounds"].append({"type": "block", "tag": "block"})

    return config
