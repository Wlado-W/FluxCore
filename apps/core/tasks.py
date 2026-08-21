"""
Celery-задачи core: health-check нод, сбор метрик, авто-restart Xray/sing-box
при падении, применение конфигов после изменений в БД.
"""
from celery import shared_task


@shared_task
def check_node_health(node_id: int):
    """TODO: опросить агент ноды, обновить Node.status и Node.last_seen_at."""
    raise NotImplementedError


@shared_task
def collect_node_metrics(node_id: int):
    """TODO: получить CPU/RAM/диск/трафик с агента, создать NodeMetric."""
    raise NotImplementedError
