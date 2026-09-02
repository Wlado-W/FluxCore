"""DRF viewsets/views for routing."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.routing.models import RoutingRule

from .serializers import RoutingRuleSerializer


class RoutingRuleViewSet(viewsets.ModelViewSet):
    """CRUD для правил маршрутизации, отсортированных по приоритету на ноде."""
    queryset = RoutingRule.objects.select_related("node", "target_outbound").all()
    serializer_class = RoutingRuleSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["node", "match_type", "is_active"]
