"""
panel_settings app — модель темы оформления панели.

Тема задаёт набор CSS-переменных (см. static/css/dashboard.css :root),
которые применяются глобально через context processor
(apps/panel_settings/context_processors.py) и рендерятся в base.html
как инлайновый <style> блок, переопределяющий значения по умолчанию.
"""
from django.db import models


class Theme(models.Model):
    name = models.CharField(max_length=100, unique=True)
    is_active = models.BooleanField(
        default=False, help_text="Только одна тема может быть активна одновременно"
    )

    # Цвета соответствуют CSS custom properties в static/css/dashboard.css :root
    color_bg = models.CharField(max_length=32, default="#0f1420", help_text="Фон страницы (--bg)")
    color_surface = models.CharField(max_length=32, default="#171d2c", help_text="Фон карточек (--surface)")
    color_border = models.CharField(max_length=32, default="#262e42", help_text="Границы (--border)")
    color_text = models.CharField(max_length=32, default="#e6e9f0", help_text="Основной текст (--text)")
    color_text_muted = models.CharField(max_length=32, default="#8891a7", help_text="Приглушённый текст (--text-muted)")
    color_accent = models.CharField(max_length=32, default="#4f7cff", help_text="Акцентный цвет, кнопки (--accent)")
    color_online = models.CharField(max_length=32, default="#33c481", help_text="Статус «онлайн» (--online)")
    color_offline = models.CharField(max_length=32, default="#6b7385", help_text="Статус «оффлайн» (--offline)")
    color_error = models.CharField(max_length=32, default="#e5484d", help_text="Статус «ошибка» (--error)")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name}{' (активна)' if self.is_active else ''}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self.is_active:
            # Гарантируем, что активна только одна тема одновременно
            Theme.objects.exclude(pk=self.pk).update(is_active=False)

    def as_css_variables(self) -> dict:
        return {
            "--bg": self.color_bg,
            "--surface": self.color_surface,
            "--border": self.color_border,
            "--text": self.color_text,
            "--text-muted": self.color_text_muted,
            "--accent": self.color_accent,
            "--online": self.color_online,
            "--offline": self.color_offline,
            "--error": self.color_error,
        }
