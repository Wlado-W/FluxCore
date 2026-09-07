from django.contrib import admin

from .models import Inbound


@admin.register(Inbound)
class InboundAdmin(admin.ModelAdmin):
    list_display = ("tag", "node", "protocol", "engine", "transport", "security", "port", "is_active")
    list_filter = ("protocol", "engine", "transport", "security", "is_active", "node")
    search_fields = ("tag", "node__name")
