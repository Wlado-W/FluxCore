import os

from django.http import FileResponse, Http404
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.licensing.tiers import LicenseTier, RequireTierPermission

from .models import BackupTask
from .serializers import (
    BackupTaskSerializer,
    CreateBackupRequestSerializer,
    RestoreBackupRequestSerializer,
)
from .services import run_restore_backup_task
from .task import create_system_backup

# Резервное копирование — фича тарифа Premium и выше (см. ТЗ блок 2, матрица тарифов).
BACKUP_PERMISSION_CLASSES = [IsAdminUser, RequireTierPermission]
BACKUP_REQUIRED_TIER = LicenseTier.PREMIUM


class BackupListView(ListAPIView):
    """GET /api/v1/backups/ — список бэкапов."""
    queryset = BackupTask.objects.select_related("created_by").all()
    serializer_class = BackupTaskSerializer
    permission_classes = BACKUP_PERMISSION_CLASSES
    required_tier = BACKUP_REQUIRED_TIER


class BackupCreateView(APIView):
    """POST /api/v1/backups/create/ — ставит создание бэкапа в очередь (Celery)."""
    permission_classes = BACKUP_PERMISSION_CLASSES
    required_tier = BACKUP_REQUIRED_TIER

    def post(self, request):
        serializer = CreateBackupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get("password") or None

        backup = BackupTask.objects.create(created_by=request.user)
        task = create_system_backup.delay(backup.id, password)

        return Response(
            {"backup_id": backup.id, "task_id": task.id, "status": "queued", "will_be_encrypted": bool(password)},
            status=202,
        )


class BackupDownloadView(APIView):
    """GET /api/v1/backups/<id>/download/ — скачивание архива бэкапа."""
    permission_classes = BACKUP_PERMISSION_CLASSES
    required_tier = BACKUP_REQUIRED_TIER

    def get(self, request, pk):
        backup = BackupTask.objects.filter(pk=pk).first()
        if backup is None or backup.status != BackupTask.Status.COMPLETED:
            raise Http404("Бэкап не найден или ещё не готов.")
        if not backup.file_path or not os.path.exists(backup.file_path):
            raise Http404("Файл бэкапа отсутствует на диске.")

        response = FileResponse(
            open(backup.file_path, "rb"),
            as_attachment=True,
            filename=backup.file_name,
            content_type="application/octet-stream",
        )
        return response


class BackupDeleteView(APIView):
    """DELETE /api/v1/backups/<id>/ — удаляет файл бэкапа и запись."""
    permission_classes = BACKUP_PERMISSION_CLASSES
    required_tier = BACKUP_REQUIRED_TIER

    def delete(self, request, pk):
        backup = BackupTask.objects.filter(pk=pk).first()
        if backup is None:
            raise Http404("Бэкап не найден.")
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        backup.delete()
        return Response(status=204)


class BackupRestoreView(APIView):
    """POST /api/v1/backups/<id>/restore/ — ставит восстановление из бэкапа в очередь."""
    permission_classes = BACKUP_PERMISSION_CLASSES
    required_tier = BACKUP_REQUIRED_TIER

    def post(self, request, pk):
        backup = BackupTask.objects.filter(pk=pk).first()
        if backup is None or backup.status != BackupTask.Status.COMPLETED:
            raise Http404("Бэкап не найден или ещё не готов.")

        serializer = RestoreBackupRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        password = serializer.validated_data.get("password") or None

        if backup.is_encrypted and not password:
            return Response(
                {"detail": "Этот бэкап зашифрован — укажите пароль для восстановления."}, status=400
            )

        task = run_restore_backup_task.delay(backup.id, password)
        return Response({"task_id": task.id, "status": "queued"}, status=202)
