"""
Celery-задачи core: health-check нод, сбор метрик, авто-restart Xray/sing-box
при падении, применение конфигов после изменений в БД.

После каждого обновления статуса/метрик — публикуем событие в channel layer
("nodes_status" group), чтобы открытые дашборды обновились в реальном времени
без перезагрузки страницы (см. apps/core/consumers.py).
"""
from asgiref.sync import async_to_sync
from celery import shared_task
from channels.layers import get_channel_layer
from django.utils import timezone

from .consumers import NODES_STATUS_GROUP
from .models import Node, NodeMetric
from .services.deploy import deploy_config_to_node, fetch_node_health, fetch_node_metrics


def _broadcast_node_update(node: Node, metric: NodeMetric | None = None):
    channel_layer = get_channel_layer()
    if channel_layer is None:
        return
    async_to_sync(channel_layer.group_send)(
        NODES_STATUS_GROUP,
        {
            "type": "node.status.update",
            "node_id": node.id,
            "status": node.status,
            "cpu_percent": metric.cpu_percent if metric else None,
            "ram_percent": metric.ram_percent if metric else None,
            "disk_percent": metric.disk_percent if metric else None,
            "last_seen_at": node.last_seen_at.isoformat() if node.last_seen_at else None,
        },
    )


@shared_task
def check_node_health(node_id: int):
    """Опрашивает агент ноды, обновляет Node.status и Node.last_seen_at."""
    try:
        node = Node.objects.get(id=node_id, is_active=True)
    except Node.DoesNotExist:
        return

    health = fetch_node_health(node)
    if health is None:
        node.status = Node.Status.OFFLINE
        node.save(update_fields=["status"])
        _broadcast_node_update(node)
        return

    engines_ok = all(health.get("engines", {}).values())
    node.status = Node.Status.ONLINE if engines_ok else Node.Status.ERROR
    node.last_seen_at = timezone.now()
    node.save(update_fields=["status", "last_seen_at"])
    _broadcast_node_update(node)


@shared_task
def collect_node_metrics(node_id: int):
    """Получает CPU/RAM/диск/трафик с агента, создаёт запись NodeMetric."""
    try:
        node = Node.objects.get(id=node_id, is_active=True)
    except Node.DoesNotExist:
        return

    data = fetch_node_metrics(node)
    if data is None:
        return

    metric = NodeMetric.objects.create(
        node=node,
        cpu_percent=data.get("cpu_percent", 0),
        ram_percent=data.get("ram_percent", 0),
        disk_percent=data.get("disk_percent", 0),
        traffic_up_bytes=data.get("traffic_up_bytes", 0),
        traffic_down_bytes=data.get("traffic_down_bytes", 0),
        uptime_seconds=data.get("uptime_seconds", 0),
    )
    _broadcast_node_update(node, metric)


@shared_task
def check_all_nodes_health():
    """Периодическая задача (Celery Beat): запускает health-check для всех активных нод."""
    for node_id in Node.objects.filter(is_active=True).values_list("id", flat=True):
        check_node_health.delay(node_id)


@shared_task
def collect_all_nodes_metrics():
    """Периодическая задача (Celery Beat): собирает метрики со всех активных нод."""
    for node_id in Node.objects.filter(is_active=True).values_list("id", flat=True):
        collect_node_metrics.delay(node_id)


@shared_task
def redeploy_node_config(node_id: int):
    """Пересобирает и отправляет конфиг на ноду (напр. после изменения Inbound/RoutingRule)."""
    try:
        node = Node.objects.get(id=node_id, is_active=True)
    except Node.DoesNotExist:
        return
    deploy_config_to_node(node)
