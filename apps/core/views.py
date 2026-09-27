"""
Views дашборда панели (серверный рендеринг). Live-обновления статуса нод
идут отдельно через WebSocket (см. consumers.py) — эта view отдаёт только
первоначальный снимок состояния при загрузке страницы.
"""
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import render
from django.template.loader import render_to_string

from .models import Node
from .services.about import get_about_info


@login_required
def about_view(request):
    return render(request, "core/about.html", {"about": get_about_info()})


@login_required
def eula_view(request):
    return render(request, "core/eula.html", {"eula_text": render_to_string("eula.txt")})


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


@login_required
def node_map_data_view(request):
    """
    Данные для карты нод на дашборде — отдельный сессионный эндпоинт
    (не DRF), т.к. основной DRF API настроен на токен-аутентификацию для
    внешних потребителей, а дашборд аутентифицирован через сессию браузера.
    """
    nodes = Node.objects.filter(is_active=True, latitude__isnull=False, longitude__isnull=False)
    data = [
        {
            "id": n.id, "name": n.name, "status": n.status,
            "country_code": n.country_code, "city": n.city, "isp": n.isp,
            "latitude": n.latitude, "longitude": n.longitude,
        }
        for n in nodes
    ]
    return JsonResponse(data, safe=False)
