from rest_framework.generics import ListAPIView, RetrieveAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import SystemPatch, UpdateHistory
from .serializers import (
    ApplyUpdateRequestSerializer,
    SystemPatchSerializer,
    UpdateHistorySerializer,
)
from .services import CURRENT_VERSION
from .tasks import run_apply_patch_task, run_full_update_task, run_update_check_task


class UpdateCheckView(APIView):
    """
    POST /api/v1/updates/check/ — ставит в очередь опрос сервера лицензий
    на предмет новой версии/патчей. Только для администраторов панели.
    """
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({"current_version": CURRENT_VERSION})

    def post(self, request):
        task = run_update_check_task.delay()
        return Response({"task_id": task.id, "status": "queued"}, status=202)


class UpdateApplyView(APIView):
    """POST /api/v1/updates/apply/ — ставит в очередь полное обновление панели."""
    permission_classes = [IsAdminUser]

    def post(self, request):
        serializer = ApplyUpdateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        task = run_full_update_task.delay(data["download_url"], data["sha256"], data["signature"])
        return Response({"task_id": task.id, "status": "queued"}, status=202)


class UpdateHistoryListView(ListAPIView):
    queryset = UpdateHistory.objects.all()
    serializer_class = UpdateHistorySerializer
    permission_classes = [IsAdminUser]


class SystemPatchListView(ListAPIView):
    queryset = SystemPatch.objects.all()
    serializer_class = SystemPatchSerializer
    permission_classes = [IsAdminUser]


class SystemPatchDetailView(RetrieveAPIView):
    queryset = SystemPatch.objects.all()
    serializer_class = SystemPatchSerializer
    permission_classes = [IsAdminUser]


class SystemPatchApplyView(APIView):
    """POST /api/v1/updates/patches/<id>/apply/ — ставит патч на выполнение."""
    permission_classes = [IsAdminUser]

    def post(self, request, pk):
        patch = SystemPatch.objects.filter(pk=pk).first()
        if patch is None:
            return Response({"detail": "Патч не найден."}, status=404)
        if patch.status == SystemPatch.Status.SUCCESS:
            return Response({"detail": "Патч уже был успешно применён."}, status=400)
        if patch.status == SystemPatch.Status.REJECTED:
            return Response(
                {"detail": "Подпись патча недействительна — выполнение запрещено."}, status=400
            )
        task = run_apply_patch_task.delay(patch.id)
        return Response({"task_id": task.id, "status": "queued"}, status=202)
