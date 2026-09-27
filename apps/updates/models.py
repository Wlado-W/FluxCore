from django.db import models
from django.utils.translation import gettext_lazy as _

class SystemPatch(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", _("Ожидает применения")
        VERIFIED = "verified", _("Подпись проверена, ожидает запуска")
        REJECTED = "rejected", _("Подпись недействительна — выполнение запрещено")
        SUCCESS = "success", _("Успешно применён")
        FAILED = "failed", _("Ошибка применения")

    class Source(models.TextChoices):
        LOCAL = "local", _("Создан локально администратором")
        REMOTE = "remote", _("Получен с сервера лицензий")

    patch_id = models.CharField(max_length=64, unique=True, help_text="Уникальный идентификатор патча, напр. patch_2026_09_v1")
    title = models.CharField(max_length=255, verbose_name=_("Название патча"))
    description = models.TextField(blank=True, verbose_name=_("Описание изменений"))
    script_content = models.TextField(help_text=_("Python или Bash скрипт для исполнения"))
    is_bash = models.BooleanField(default=False, help_text=_("Если True — исполняется как bash-скрипт, иначе — Python в контексте Django"))
    source = models.CharField(
        max_length=10, choices=Source.choices, default=Source.LOCAL,
        help_text=_("Патчи с source=remote выполняются только после проверки подписи (см. signature)."),
    )
    signature = models.TextField(
        blank=True,
        help_text=_("Ed25519-подпись sha256(script_content) от сервера лицензий (только для source=remote)."),
    )
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


class UpdateHistory(models.Model):
    """Журнал попыток полного обновления панели (для 'О программе' и аудита)."""

    class Status(models.TextChoices):
        STARTED = "started", _("Запущено")
        SUCCESS = "success", _("Успешно")
        FAILED = "failed", _("Ошибка")

    from_version = models.CharField(max_length=32)
    to_version = models.CharField(max_length=32)
    download_url = models.URLField(max_length=512)
    sha256 = models.CharField(max_length=64)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.STARTED)
    message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("История обновлений")
        verbose_name_plural = _("История обновлений")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.from_version} → {self.to_version} [{self.status}]"
