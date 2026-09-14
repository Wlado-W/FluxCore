from django.contrib import admin

from .models import License, RemoteActivationToken


@admin.register(License)
class LicenseAdmin(admin.ModelAdmin):
    list_display = ("customer_name", "max_nodes", "expires_at", "activated_at")
    readonly_fields = ("key", "customer_name", "max_nodes", "expires_at", "last_checked_at", "activated_at")

    def has_add_permission(self, request):
        return False  # активация только через management-команду activate_license

    def has_change_permission(self, request, obj=None):
        return False

@admin.register(RemoteActivationToken)
class RemoteActivationTokenAdmin(admin.ModelAdmin):
    list_display = ("token", "max_nodes", "issued_at", "expires_at", "fetched_at")
    readonly_fields = ("token", "max_nodes", "issued_at", "expires_at", "fetched_at")

    def has_add_permission(self, request):
        return False  # активация только через management-команду activate_license

    def has_change_permission(self, request, obj=None):
        return False
