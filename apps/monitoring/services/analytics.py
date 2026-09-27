"""
Аналитика поверх NodeMetric и Client: тепловая карта нагрузки по нодам
и времени суток, топ клиентов по потреблению трафика, прогноз ёмкости
(простая линейная регрессия по истории метрик).
"""
from datetime import timedelta

from django.db.models import Avg
from django.db.models.functions import ExtractHour, ExtractWeekDay
from django.utils import timezone

from apps.clients.models import Client
from apps.core.models import Node, NodeMetric


def get_load_heatmap(node: Node | None = None, days: int = 7) -> list[dict]:
    """
    Средняя загрузка CPU/RAM по дню недели и часу суток за последние `days`
    дней — данные для тепловой карты на дашборде.

    Возвращает список {weekday, hour, avg_cpu, avg_ram}, weekday — 1..7
    (1 = воскресенье, как в Django ExtractWeekDay).
    """
    since = timezone.now() - timedelta(days=days)
    qs = NodeMetric.objects.filter(recorded_at__gte=since)
    if node is not None:
        qs = qs.filter(node=node)

    qs = (
        qs.annotate(weekday=ExtractWeekDay("recorded_at"), hour=ExtractHour("recorded_at"))
        .values("weekday", "hour")
        .annotate(avg_cpu=Avg("cpu_percent"), avg_ram=Avg("ram_percent"))
        .order_by("weekday", "hour")
    )
    return list(qs)


def get_top_clients_by_traffic(limit: int = 10):
    """Клиенты с наибольшим потреблённым трафиком (traffic_used_bytes)."""
    return (
        Client.objects.select_related("owner", "group")
        .order_by("-traffic_used_bytes")[:limit]
    )


def _linear_regression(points: list[tuple[float, float]]) -> tuple[float, float]:
    """
    Простая линейная регрессия методом наименьших квадратов без внешних
    зависимостей. points — [(x, y), ...]. Возвращает (slope, intercept).
    """
    n = len(points)
    if n < 2:
        return 0.0, points[0][1] if points else 0.0

    sum_x = sum(p[0] for p in points)
    sum_y = sum(p[1] for p in points)
    sum_xy = sum(p[0] * p[1] for p in points)
    sum_xx = sum(p[0] ** 2 for p in points)

    denominator = n * sum_xx - sum_x ** 2
    if denominator == 0:
        return 0.0, sum_y / n

    slope = (n * sum_xy - sum_x * sum_y) / denominator
    intercept = (sum_y - slope * sum_x) / n
    return slope, intercept


def forecast_metric_trend(
    node: Node, field: str = "disk_percent", threshold: float = 90.0, lookback_days: int = 14
) -> dict:
    """
    Прогнозирует, через сколько дней метрика `field` (disk_percent,
    cpu_percent, ram_percent) достигнет `threshold`, на основе линейного
    тренда за последние `lookback_days` дней. Если тренд не растёт или
    метрика уже выше порога — days_until_threshold будет None/0
    соответственно.
    """
    since = timezone.now() - timedelta(days=lookback_days)
    metrics = list(
        NodeMetric.objects.filter(node=node, recorded_at__gte=since)
        .order_by("recorded_at")
        .values("recorded_at", field)
    )

    if len(metrics) < 2:
        return {
            "field": field, "current_value": metrics[-1][field] if metrics else None,
            "slope_per_day": None, "days_until_threshold": None,
            "message": "Недостаточно данных для прогноза (нужно хотя бы 2 замера).",
        }

    first_ts = metrics[0]["recorded_at"]
    points = [
        ((m["recorded_at"] - first_ts).total_seconds() / 86400, m[field])
        for m in metrics
    ]

    slope, intercept = _linear_regression(points)
    current_value = points[-1][1]
    current_x = points[-1][0]

    days_until_threshold = None
    if slope > 0 and current_value < threshold:
        # threshold = slope * x + intercept  =>  x = (threshold - intercept) / slope
        target_x = (threshold - intercept) / slope
        days_until_threshold = round(target_x - current_x, 1)
        if days_until_threshold < 0:
            days_until_threshold = 0

    return {
        "field": field,
        "current_value": round(current_value, 1),
        "slope_per_day": round(slope, 4),
        "days_until_threshold": days_until_threshold,
        "threshold": threshold,
    }
