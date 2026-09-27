"""DRF serializers for routing."""
from rest_framework import serializers

from apps.routing.models import RoutingRule


class RoutingRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoutingRule
        fields = [
            "id", "node", "name", "priority", "match_type", "match_values",
            "target_outbound", "target_balancer_tag", "is_active",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        target_outbound = attrs.get("target_outbound", getattr(self.instance, "target_outbound", None))
        target_balancer_tag = attrs.get(
            "target_balancer_tag", getattr(self.instance, "target_balancer_tag", "")
        )
        if not target_outbound and not target_balancer_tag:
            raise serializers.ValidationError(
                "Нужно указать либо target_outbound, либо target_balancer_tag."
            )
        return attrs
