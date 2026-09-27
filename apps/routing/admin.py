from django.contrib import admin

from .models import RoutingRule


@admin.register(RoutingRule)
class RoutingRuleAdmin(admin.ModelAdmin):
    list_display = ("name", "node", "match_type", "priority", "target_outbound", "target_balancer_tag", "is_active")
    list_filter = ("match_type", "is_active", "node")
    search_fields = ("name", "node__name")
    ordering = ("node", "priority")
