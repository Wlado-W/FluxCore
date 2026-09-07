from django.contrib import admin

from .models import Node, NodeGroup, NodeMetric


@admin.register(NodeGroup)
class NodeGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_cascade", "created_at")
    search_fields = ("name",)


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "group", "status", "is_active", "last_seen_at")
    list_filter = ("status", "is_active", "group")
    search_fields = ("name", "address")
    readonly_fields = ("agent_token", "created_at", "updated_at")


@admin.register(NodeMetric)
class NodeMetricAdmin(admin.ModelAdmin):
    list_display = ("node", "cpu_percent", "ram_percent", "disk_percent", "recorded_at")
    list_filter = ("node",)
    ordering = ("-recorded_at",)
