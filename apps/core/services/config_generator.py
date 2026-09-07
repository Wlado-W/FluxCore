"""
Единая точка входа для генерации конфигов движков (Xray-core / sing-box)
на основе моделей Node / Inbound / Outbound / RoutingRule.

Использование:
    from apps.core.services.config_generator import build_engine_config, build_all_configs

    xray_config = build_engine_config(node, "xray")
    all_configs = build_all_configs(node)  # {"xray": {...}, "sing-box": {...}}
"""
from apps.core.models import Node

from .singbox_builder import build_singbox_config
from .xray_builder import build_xray_config

_BUILDERS = {
    Node.Engine.XRAY: build_xray_config,
    Node.Engine.SING_BOX: build_singbox_config,
}


def build_engine_config(node: Node, engine: str) -> dict:
    """Собирает конфиг для одного конкретного движка на ноде."""
    builder = _BUILDERS.get(engine)
    if builder is None:
        raise ValueError(f"Неизвестный движок: {engine}")
    return builder(node)


def build_all_configs(node: Node) -> dict[str, dict]:
    """
    Собирает конфиги для всех движков, включённых на ноде
    (node.engines_enabled), в виде {engine_name: config_dict}.
    """
    return {
        engine: build_engine_config(node, engine)
        for engine in node.engines_enabled
        if engine in _BUILDERS
    }
