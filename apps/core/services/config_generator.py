"""
Генерация конфигов для движков (Xray-core / v2core, sing-box) на основе
моделей Node / Inbound / Outbound / RoutingRule.

TODO:
- build_xray_config(node) -> dict
- build_singbox_config(node) -> dict
- Общая точка входа build_engine_config(node, engine) -> dict, которая
  делегирует нужному билдеру в зависимости от node.engines_enabled.
"""


def build_engine_config(node, engine: str) -> dict:
    raise NotImplementedError
