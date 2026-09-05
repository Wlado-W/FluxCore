"""
Data-миграция: создаёт две готовые темы «из коробки» — тёмную (по умолчанию,
совпадает с текущим static/css/dashboard.css) и светлую. Тёмная ставится
активной, чтобы поведение не менялось для тех, кто уже пользуется панелью.
"""
from django.db import migrations


def create_default_themes(apps, schema_editor):
    Theme = apps.get_model("panel_settings", "Theme")

    Theme.objects.get_or_create(
        name="FluxCore Dark",
        defaults={
            "is_active": True,
            "color_bg": "#0f1420",
            "color_surface": "#171d2c",
            "color_border": "#262e42",
            "color_text": "#e6e9f0",
            "color_text_muted": "#8891a7",
            "color_accent": "#4f7cff",
            "color_online": "#33c481",
            "color_offline": "#6b7385",
            "color_error": "#e5484d",
        },
    )

    Theme.objects.get_or_create(
        name="FluxCore Light",
        defaults={
            "is_active": False,
            "color_bg": "#f4f6fb",
            "color_surface": "#ffffff",
            "color_border": "#dde2ee",
            "color_text": "#1a1f2e",
            "color_text_muted": "#6b7385",
            "color_accent": "#3b63e0",
            "color_online": "#1f9d63",
            "color_offline": "#9aa1b3",
            "color_error": "#d13d42",
        },
    )


def remove_default_themes(apps, schema_editor):
    Theme = apps.get_model("panel_settings", "Theme")
    Theme.objects.filter(name__in=["FluxCore Dark", "FluxCore Light"]).delete()


class Migration(migrations.Migration):
    dependencies = [
        ("panel_settings", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(create_default_themes, remove_default_themes),
    ]
