"""
Сборка ссылок-конфигов (vless://, vmess://, trojan:// и т.п.) для конкретного
клиента на конкретном inbound'е — то, что попадает в подписку и что можно
вставить в v2rayNG/Happ/Shadowrocket напрямую.

Каждая функция строит один URI/конфиг для пары (Client, Inbound).
Адрес сервера берётся из Inbound.node.address, порт — из Inbound.port.
"""
import base64
import json
from urllib.parse import quote, urlencode


def _security_query_params(inbound) -> dict:
    """Общие query-параметры транспорта/безопасности для vless/trojan-подобных ссылок."""
    params = {"type": inbound.transport}

    if inbound.security == "tls":
        params["security"] = "tls"
        sni = inbound.security_settings.get("serverName") or inbound.security_settings.get("sni")
        if sni:
            params["sni"] = sni
        fp = inbound.security_settings.get("fingerprint")
        if fp:
            params["fp"] = fp
    elif inbound.security == "reality":
        params["security"] = "reality"
        rs = inbound.security_settings
        if rs.get("serverNames"):
            params["sni"] = rs["serverNames"][0]
        if rs.get("publicKey"):
            params["pbk"] = rs["publicKey"]
        if rs.get("shortIds"):
            params["sid"] = rs["shortIds"][0]
        if rs.get("fingerprint"):
            params["fp"] = rs["fingerprint"]
    else:
        params["security"] = "none"

    ts = inbound.transport_settings or {}
    if inbound.transport == "ws":
        if ts.get("path"):
            params["path"] = ts["path"]
        if ts.get("host"):
            params["host"] = ts["host"]
    elif inbound.transport == "grpc":
        if ts.get("serviceName"):
            params["serviceName"] = ts["serviceName"]
    elif inbound.transport in ("xhttp", "httpupgrade"):
        if ts.get("path"):
            params["path"] = ts["path"]
        if ts.get("host"):
            params["host"] = ts["host"]

    return params


def build_vless_link(client, inbound) -> str:
    node = inbound.node
    params = _security_query_params(inbound)
    if inbound.transport_settings.get("flow"):
        params["flow"] = inbound.transport_settings["flow"]
    query = urlencode(params)
    label = quote(f"{node.name}-{client.name}")
    return f"vless://{client.uuid}@{node.address}:{inbound.port}?{query}#{label}"


def build_vmess_link(client, inbound) -> str:
    node = inbound.node
    vmess_obj = {
        "v": "2",
        "ps": f"{node.name}-{client.name}",
        "add": node.address,
        "port": str(inbound.port),
        "id": str(client.uuid),
        "aid": "0",
        "net": inbound.transport,
        "type": "none",
        "host": (inbound.transport_settings or {}).get("host", ""),
        "path": (inbound.transport_settings or {}).get("path", ""),
        "tls": "tls" if inbound.security == "tls" else "",
        "sni": (inbound.security_settings or {}).get("serverName", ""),
    }
    encoded = base64.b64encode(json.dumps(vmess_obj).encode()).decode()
    return f"vmess://{encoded}"


def build_trojan_link(client, inbound) -> str:
    node = inbound.node
    params = _security_query_params(inbound)
    query = urlencode(params)
    label = quote(f"{node.name}-{client.name}")
    return f"trojan://{client.password}@{node.address}:{inbound.port}?{query}#{label}"


def build_shadowsocks_link(client, inbound) -> str:
    node = inbound.node
    method = (inbound.transport_settings or {}).get("method", "chacha20-ietf-poly1305")
    userinfo = base64.b64encode(f"{method}:{client.password}".encode()).decode()
    label = quote(f"{node.name}-{client.name}")
    return f"ss://{userinfo}@{node.address}:{inbound.port}#{label}"


def build_hysteria2_link(client, inbound) -> str:
    node = inbound.node
    params = {}
    sni = (inbound.security_settings or {}).get("serverName")
    if sni:
        params["sni"] = sni
    query = urlencode(params)
    label = quote(f"{node.name}-{client.name}")
    suffix = f"?{query}" if query else ""
    return f"hysteria2://{client.password}@{node.address}:{inbound.port}{suffix}#{label}"


def build_tuic_link(client, inbound) -> str:
    node = inbound.node
    params = {"congestion_control": "bbr"}
    sni = (inbound.security_settings or {}).get("serverName")
    if sni:
        params["sni"] = sni
    query = urlencode(params)
    label = quote(f"{node.name}-{client.name}")
    return f"tuic://{client.uuid}:{client.password}@{node.address}:{inbound.port}?{query}#{label}"


def build_wireguard_config(client, inbound) -> str:
    """
    WireGuard не укладывается в схему URI-ссылок — клиенту нужен полноценный
    .conf файл. Возвращаем его текстом (клиент сам решает, показать как
    файл для скачивания или QR).
    """
    node = inbound.node
    server_public_key = (inbound.security_settings or {}).get("publicKey", "")
    return (
        "[Interface]\n"
        f"PrivateKey = {client.wg_private_key}\n"
        f"Address = {client.wg_allowed_ips}\n"
        "DNS = 1.1.1.1\n\n"
        "[Peer]\n"
        f"PublicKey = {server_public_key}\n"
        f"Endpoint = {node.address}:{inbound.port}\n"
        "AllowedIPs = 0.0.0.0/0, ::/0\n"
        "PersistentKeepalive = 25\n"
    )


_LINK_BUILDERS = {
    "vless": build_vless_link,
    "vmess": build_vmess_link,
    "trojan": build_trojan_link,
    "shadowsocks": build_shadowsocks_link,
    "hysteria2": build_hysteria2_link,
    "tuic": build_tuic_link,
}


def build_link_for_inbound(client, inbound) -> str | None:
    """Возвращает готовую ссылку для протокола inbound'а, либо None, если протокол не поддерживает URI-схему."""
    builder = _LINK_BUILDERS.get(inbound.protocol)
    if builder:
        return builder(client, inbound)
    return None
