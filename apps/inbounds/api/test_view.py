"""One-click тест соединения для inbound'а."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.inbounds.models import Inbound
from apps.inbounds.services.connectivity import test_inbound_connection


class InboundTestConnectionView(APIView):
    """POST /api/inbounds/<id>/test/ — проверяет доступность порта (+ TLS-handshake, если включён)."""
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        try:
            inbound = Inbound.objects.select_related("node").get(pk=pk)
        except Inbound.DoesNotExist:
            return Response({"detail": "Inbound не найден."}, status=404)

        result = test_inbound_connection(inbound)
        return Response(result)
