from django.contrib import admin

from .models import Node, NodeGroup, NodeMetric


@admin.register(NodeGroup)
class NodeGroupAdmin(admin.ModelAdmin):
    list_display = ("name", "is_cascade", "created_at")
    search_fields = ("name",)


@admin.register(Node)
class NodeAdmin(admin.ModelAdmin):
    list_display = ("name", "address", "country_code", "city", "group", "status", "is_active", "last_seen_at")
    list_filter = ("status", "is_active", "group", "country_code")
    search_fields = ("name", "address", "city", "isp")
    readonly_fields = ("agent_token", "created_at", "updated_at", "country_code", "city", "isp", "latitude", "longitude", "geo_resolved_at")


@admin.register(NodeMetric)
class NodeMetricAdmin(admin.ModelAdmin):
    list_display = ("node", "cpu_percent", "ram_percent", "disk_percent", "recorded_at")
    list_filter = ("node",)
    ordering = ("-recorded_at",)
