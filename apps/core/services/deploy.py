"""
Доставка сгенерированного конфига на ноду через агент и применение
(перезапуск нужного движка).

Агент слушает на node.port_agent и принимает конфиг + команду restart
по HTTP/REST, аутентификация — по node.agent_token.
"""
import requests
from requests.exceptions import RequestException

from apps.core.models import Node

from .config_generator import build_all_configs


def deploy_config_to_node(node: Node, timeout: int = 10) -> bool:
    """
    Собирает конфиги для всех включённых на ноде движков и отправляет
    их агенту для применения. Возвращает True при успехе.
    """
    configs = build_all_configs(node)
    if not configs:
        return False

    url = f"https://{node.address}:{node.port_agent}/apply-config"
    headers = {"Authorization": f"Bearer {node.agent_token}"}

    try:
        response = requests.post(
            url, json={"configs": configs}, headers=headers, timeout=timeout
        )
        response.raise_for_status()
    except RequestException:
        # TODO: залогировать ошибку, обновить Node.status = ERROR
        return False

    return True


def deploy_to_nodes(nodes) -> dict[int, bool]:
    """Массовая доставка конфигов на несколько нод (напр. после изменения RoutingRule)."""
    return {node.id: deploy_config_to_node(node) for node in nodes}
