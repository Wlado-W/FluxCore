"""Дашборд-страницы для резервного копирования (не DRF — сессионная аутентификация)."""
import os

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render

from apps.licensing.tiers import LicenseTier, check_tier_access

from .models import BackupTask
from .services import run_restore_backup_task
from .task import create_system_backup

BACKUP_UPGRADE_MESSAGE = "Резервное копирование доступно на тарифе Premium и выше."


def _require_premium(request) -> bool:
    """
    Единая проверка тарифа для всех backup-страниц дашборда — по стилю,
    уже принятому в client_create_view/node_create_view (сообщение +
    редирект), а не через @require_tier (тот удобнее для DRF/точечных
    action'ов, но для целой группы страниц читаемее явная проверка).
    """
    if not check_tier_access(LicenseTier.PREMIUM):
        messages.error(request, BACKUP_UPGRADE_MESSAGE)
        return False
    return True


@login_required
def backup_list_view(request):
    if not _require_premium(request):
        return redirect("dashboard:index")
    backups = BackupTask.objects.select_related("created_by").all()
    return render(request, "backup/backup_list.html", {"backups": backups})


@login_required
def backup_create_view(request):
    if not _require_premium(request):
        return redirect("dashboard:index")

    if request.method == "POST":
        password = request.POST.get("password", "").strip()
        if password and len(password) < 8:
            messages.error(request, "Пароль для шифрования должен быть не короче 8 символов.")
            return redirect("dashboard:backup-list")

        backup = BackupTask.objects.create(created_by=request.user)
        create_system_backup.delay(backup.id, password or None)

        if password:
            messages.success(request, "Создание зашифрованного бэкапа запущено. Обновите страницу через минуту.")
        else:
            messages.warning(
                request,
                "Создание бэкапа запущено БЕЗ шифрования — файл будет читаемым для любого, у кого есть доступ к диску.",
            )

    return redirect("dashboard:backup-list")


@login_required
def backup_download_view(request, pk):
    if not _require_premium(request):
        return redirect("dashboard:index")

    backup = get_object_or_404(BackupTask, pk=pk)
    if backup.status != BackupTask.Status.COMPLETED or not backup.file_path or not os.path.exists(backup.file_path):
        raise Http404("Файл бэкапа недоступен.")
    return FileResponse(
        open(backup.file_path, "rb"), as_attachment=True, filename=backup.file_name,
    )


@login_required
def backup_delete_view(request, pk):
    if not _require_premium(request):
        return redirect("dashboard:index")

    backup = get_object_or_404(BackupTask, pk=pk)
    if request.method == "POST":
        if backup.file_path and os.path.exists(backup.file_path):
            os.remove(backup.file_path)
        backup.delete()
        messages.success(request, "Бэкап удалён.")
    return redirect("dashboard:backup-list")


@login_required
def backup_restore_view(request, pk):
    if not _require_premium(request):
        return redirect("dashboard:index")

    backup = get_object_or_404(BackupTask, pk=pk)

    if request.method == "POST":
        if backup.status != BackupTask.Status.COMPLETED:
            messages.error(request, "Этот бэкап ещё не готов.")
            return redirect("dashboard:backup-list")

        if not request.POST.get("confirm"):
            messages.error(request, "Подтвердите, что понимаете: восстановление перезапишет текущую базу данных.")
            return redirect("dashboard:backup-list")

        password = request.POST.get("password", "").strip()
        if backup.is_encrypted and not password:
            messages.error(request, "Этот бэкап зашифрован — укажите пароль для восстановления.")
            return redirect("dashboard:backup-list")

        run_restore_backup_task.delay(backup.id, password or None)
        messages.success(request, "Восстановление запущено в фоне. Панель может стать недоступна на время операции.")

    return redirect("dashboard:backup-list")
