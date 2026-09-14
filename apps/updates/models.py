from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemPatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает применения")
        SUCCESS = "success", _("Успешно применён")
        FAILED = "failed", _("Ошибка применения")

    patch_id = models.CharField(max_length=64, unique=True, help_text="Уникальный идентификатор патча, напр. patch_2026_09_v1")
    title = models.CharField(max_length=255, verbose_name=_("Название патча"))
    description = models.TextField(blank=True, verbose_name=_("Описание изменений"))
    script_content = models.TextField(help_text=_("Python или Bash скрипт для исполнения"))
    is_bash = models.BooleanField(default=False, help_text=_("Если True — исполняется как bash-скрипт, иначе — Python в контексте Django"))
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    applied_at = models.DateTimeField(null=True, blank=True)
    logs = models.TextField(blank=True, verbose_name=_("Логи выполнения"))
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = _("Системный патч")
        verbose_name_plural = _("Системные патчи")
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.status.upper()}] {self.patch_id} - {self.title}"
