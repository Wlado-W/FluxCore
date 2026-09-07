"""DRF viewsets/views for outbounds."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from apps.outbounds.models import Outbound

from .serializers import OutboundSerializer


class OutboundViewSet(viewsets.ModelViewSet):
    """CRUD для исходящих. Доступ — только авторизованным (admin/agent)."""
    queryset = Outbound.objects.select_related("node", "target_node").all()
    serializer_class = OutboundSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["node", "protocol", "engine", "is_active", "balancer_tag"]
