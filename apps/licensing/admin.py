from django.contrib import admin

from .models import License


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "max_nodes", "is_valid", "expires_at", "activated_at")
    readonly_fields = ("key", "customer_name", "max_nodes", "issued_at", "expires_at", "is_valid", "last_checked_at", "activated_at")

    def has_add_permission(self, request):
        return False  # активация только через management-команду activate_license

    def has_change_permission(self, request, obj=None):
        return False
