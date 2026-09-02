"""DRF serializers for outbounds."""
from rest_framework import serializers

from apps.outbounds.models import Outbound


class OutboundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Outbound
        fields = [
            "id", "node", "engine", "tag", "protocol",
            "target_node", "target_inbound_tag",
            "settings", "stream_settings", "sockopt",
            "balancer_tag", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
