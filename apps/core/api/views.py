"""DRF viewsets/views for core."""
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.models import Node

from .serializers import NodeRegisterSerializer, NodeSerializer


class NodeViewSet(viewsets.ModelViewSet):
    """CRUD для нод — доступен только авторизованным администраторам панели."""
    queryset = Node.objects.select_related("group").all()
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["group", "status", "is_active"]


class NodeRegisterView(APIView):
    """
    Самостоятельная регистрация/подтверждение ноды агентом при первом запуске
    install.sh. Аутентификация — не через обычного DRF-пользователя, а через
    agent_token, который сверяется с уже существующей (созданной админом
    заранее в панели) записью Node.
    """
    permission_classes = []  # аутентификация кастомная, через токен ниже
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "agent"

    def post(self, request):
        auth_header = request.headers.get("Authorization", "")
        token = auth_header.removeprefix("Bearer ").strip()

        try:
            node = Node.objects.get(agent_token=token)
        except Node.DoesNotExist:
            return Response({"detail": "Неверный agent_token."}, status=401)

        serializer = NodeRegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        node.address = serializer.validated_data["address"]
        if "agent_port" in serializer.validated_data:
            node.port_agent = serializer.validated_data["agent_port"]
        node.status = Node.Status.ONLINE
        node.last_seen_at = timezone.now()
        node.save(update_fields=["address", "port_agent", "status", "last_seen_at"])

        return Response({"status": "registered", "node_id": node.id})
