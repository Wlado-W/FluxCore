import os
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

class BackupTask(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("В очереди")
        PROCESSING = "processing", _("Создаётся")
        COMPLETED = "completed", _("Завершено")
        FAILED = "failed", _("Ошибка")
        RESTORING = "restoring", _("Восстанавливается")
        RESTORED = "restored", _("Восстановлено")
        RESTORE_FAILED = "restore_failed", _("Ошибка восстановления")

    file_name = models.CharField(max_length=255, blank=True, verbose_name=_("Имя файла"))
    file_path = models.CharField(max_length=512, blank=True, verbose_name=_("Путь к файлу"))
    file_size = models.BigIntegerField(default=0, verbose_name=_("Размер (байты)"))
    is_encrypted = models.BooleanField(default=False, verbose_name=_("Зашифрован паролем"))
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL,
        related_name="backup_tasks", verbose_name=_("Создал"),
    )
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    error_message = models.TextField(blank=True, verbose_name=_("Текст ошибки"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Резервная копия")
        verbose_name_plural = _("Резервные копии")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.file_name or f'backup-{self.pk}'} [{self.status}]"