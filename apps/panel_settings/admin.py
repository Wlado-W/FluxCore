from django.contrib import admin

from .models import SystemBranding, Theme


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


@admin.register(SystemBranding)
class SystemBrandingAdmin(admin.ModelAdmin):
    list_display = ("app_name", "ad_enabled")
    fieldsets = (
        ("White Label (только Corporate)", {"fields": ("app_name", "logo", "favicon", "custom_css")}),
        ("Рекламный блок (только Corporate)", {"fields": ("ad_enabled", "ad_title", "ad_content", "ad_link")}),
    )

    def has_add_permission(self, request):
        # Singleton — запись уже создаётся через SystemBranding.load()
        return not SystemBranding.objects.exists()
