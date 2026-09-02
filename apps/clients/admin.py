from django.contrib import admin

from .models import Client, ClientGroup


@admin.register(ClientGroup)
class ClientGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "created_at")
    filter_horizontal = ("inbounds",)
    search_fields = ("name",)


@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = (
        "name", "owner", "group", "is_active", "is_trial",
        "traffic_used_bytes", "traffic_limit_bytes", "expires_at",
    )
    list_filter = ("is_active", "is_trial", "group")
    search_fields = ("name", "uuid", "owner__username")
    readonly_fields = ("uuid", "created_at", "updated_at")
