from django.contrib import admin

from .models import Outbound


@admin.register(Outbound)
class OutboundAdmin(admin.ModelAdmin):
    list_display = ("tag", "node", "protocol", "engine", "target_node", "balancer_tag", "is_active")
    list_filter = ("protocol", "engine", "is_active", "node")
    search_fields = ("tag", "node__name")
