"""DRF viewsets/views for core."""
from django.template.loader import render_to_string
from django.utils import timezone
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from apps.core.models import Node
from apps.core.services.about import get_about_info
from apps.core.tasks import resolve_node_geo

from .serializers import NodeRegisterSerializer, NodeSerializer

class NodeViewSet(viewsets.ModelViewSet):
    """CRUD для нод — доступен только авторизованным администраторам панели."""
    queryset = Node.objects.select_related("group").all()
    serializer_class = NodeSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["group", "status", "is_active"]

    def perform_create(self, serializer):
        node = serializer.save()
        # Страна/город/координаты/ISP определяются автоматически, не через API
        resolve_node_geo.delay(node.id)


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

        address_changed = node.address != serializer.validated_data["address"]
        node.address = serializer.validated_data["address"]
        if "agent_port" in serializer.validated_data:
            node.port_agent = serializer.validated_data["agent_port"]
        node.status = Node.Status.ONLINE
        node.last_seen_at = timezone.now()
        node.save(update_fields=["address", "port_agent", "status", "last_seen_at"])

        # "При опросе сервера" (ТЗ, блок 4) — самоregистрация агента часто
        # сообщает реальный публичный адрес впервые или после его смены.
        if address_changed or node.geo_resolved_at is None:
            resolve_node_geo.delay(node.id)

        return Response({"status": "registered", "node_id": node.id})


class AboutSystemView(APIView):
    """GET /api/v1/system/about/ — версия, статус лицензии, тариф, ссылка на EULA (ТЗ блок 6)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(get_about_info())


class EULAView(APIView):
    """GET /api/v1/system/eula/ — текст Лицензионного соглашения. Публичный эндпоинт
    (нужен и до входа в панель — например, для install.sh на этапе согласия)."""
    permission_classes = []

    def get(self, request):
        eula_text = render_to_string("eula.txt")
        return Response({"eula_text": eula_text})
