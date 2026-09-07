from django.contrib import admin

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ("created_at", "actor", "action", "model_name", "object_repr", "ip_address")
    list_filter = ("action", "model_name")
    search_fields = ("object_repr", "actor__username", "ip_address")
    readonly_fields = ("actor", "action", "model_name", "object_id", "object_repr", "changes", "ip_address", "created_at")
    ordering = ("-created_at",)

    def has_add_permission(self, request):
        return False  # лог создаётся только автоматически, вручную — нельзя

    def has_change_permission(self, request, obj=None):
        return False  # лог неизменяем
