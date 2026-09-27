"""
Celery-задачи модуля обновлений. Проверка/применение обновлений и патчей
может занимать десятки секунд — их запуск СИНХРОННО внутри HTTP-запроса
недопустим (таймауты воркера, зависший запрос в браузере админа).
"""
from celery import shared_task

from .models import SystemPatch
from .services import UpdateManager


@shared_task(bind=True, max_retries=0)
def run_update_check_task(self):
    return UpdateManager.check_for_updates()


@shared_task(bind=True, max_retries=0, soft_time_limit=600, time_limit=660)
def run_full_update_task(self, download_url: str, sha256_hex: str, signature_b64: str):
    return UpdateManager.perform_full_update(download_url, sha256_hex, signature_b64)


@shared_task(bind=True, max_retries=0, soft_time_limit=300, time_limit=330)
def run_apply_patch_task(self, patch_id: int):
    try:
        patch = SystemPatch.objects.get(pk=patch_id)
    except SystemPatch.DoesNotExist:
        return {"success": False, "error": "Патч не найден."}
    success = UpdateManager.apply_patch(patch)
    return {"success": success, "status": patch.status}
