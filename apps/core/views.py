"""
Views дашборда панели (серверный рендеринг). Live-обновления статуса нод
идут отдельно через WebSocket (см. consumers.py) — эта view отдаёт только
первоначальный снимок состояния при загрузке страницы.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from .models import Node, NodeMetric


@login_required
def dashboard_view(request):
    nodes = Node.objects.select_related("group").order_by("name")

    total_nodes = nodes.count()
    online_nodes = nodes.filter(status=Node.Status.ONLINE).count()
    offline_nodes = nodes.filter(status=Node.Status.OFFLINE).count()
    error_nodes = nodes.filter(status=Node.Status.ERROR).count()

    # Последняя метрика по каждой ноде — для начальной отрисовки карточек
    nodes_with_metrics = []
    for node in nodes:
        latest_metric = node.metrics.order_by("-recorded_at").first()
        nodes_with_metrics.append({"node": node, "metric": latest_metric})

    context = {
        "nodes_with_metrics": nodes_with_metrics,
        "total_nodes": total_nodes,
        "online_nodes": online_nodes,
        "offline_nodes": offline_nodes,
        "error_nodes": error_nodes,
    }
    return render(request, "dashboard/index.html", context)
