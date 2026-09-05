from django.contrib import admin

from .models import Theme


@admin.register(Theme)
class ThemeAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active", "color_bg", "color_accent", "updated_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    fieldsets = (
        (None, {"fields": ("name", "is_active")}),
        ("Цвета", {
            "fields": (
                "color_bg", "color_surface", "color_border",
                "color_text", "color_text_muted", "color_accent",
                "color_online", "color_offline", "color_error",
            )
        }),
    )
