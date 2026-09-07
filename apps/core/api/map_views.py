"""View для карты нод на дашборде: отдаёт гео-координаты + статус."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.models import Node


class NodeMapView(APIView):
    """GET /api/agent/nodes/map/ — координаты и статус всех активных нод."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        nodes = Node.objects.filter(is_active=True, latitude__isnull=False, longitude__isnull=False)
        data = [
            {
                "id": n.id, "name": n.name, "status": n.status,
                "country_code": n.country_code,
                "latitude": n.latitude, "longitude": n.longitude,
            }
            for n in nodes
        ]
        return Response(data)
