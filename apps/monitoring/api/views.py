"""DRF views for monitoring analytics: heatmap, топ клиентов, прогноз ёмкости."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Node
from apps.monitoring.services.analytics import (
    forecast_metric_trend,
    get_load_heatmap,
    get_top_clients_by_traffic,
)

from .serializers import ForecastSerializer, HeatmapEntrySerializer, TopClientSerializer


class LoadHeatmapView(APIView):
    """GET /api/monitoring/heatmap/?node=<id>&days=7 — средняя загрузка по дню недели и часу."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        node = None
        node_id = request.query_params.get("node")
        if node_id:
            node = Node.objects.filter(id=node_id).first()
            if node is None:
                return Response({"detail": "Нода не найдена."}, status=404)

        days = int(request.query_params.get("days", 7))
        data = get_load_heatmap(node=node, days=days)
        return Response(HeatmapEntrySerializer(data, many=True).data)


class TopClientsView(APIView):
    """GET /api/monitoring/top-clients/?limit=10 — клиенты с наибольшим потреблением трафика."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        limit = int(request.query_params.get("limit", 10))
        clients = get_top_clients_by_traffic(limit=limit)
        return Response(TopClientSerializer(clients, many=True).data)


class NodeForecastView(APIView):
    """GET /api/monitoring/forecast/<node_id>/?field=disk_percent&threshold=90&days=14"""
    permission_classes = [IsAuthenticated]

    def get(self, request, node_id):
        try:
            node = Node.objects.get(id=node_id)
        except Node.DoesNotExist:
            return Response({"detail": "Нода не найдена."}, status=404)

        field = request.query_params.get("field", "disk_percent")
        if field not in ("cpu_percent", "ram_percent", "disk_percent"):
            return Response({"detail": "Недопустимое поле метрики."}, status=400)

        threshold = float(request.query_params.get("threshold", 90))
        lookback_days = int(request.query_params.get("days", 14))

        result = forecast_metric_trend(node, field=field, threshold=threshold, lookback_days=lookback_days)
        return Response(ForecastSerializer(result).data)
