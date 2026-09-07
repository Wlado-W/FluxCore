"""DRF serializers for core."""
from rest_framework import serializers

from apps.core.models import Node, NodeGroup


class NodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Node
        fields = [
            "id", "name", "group", "address", "port_agent", "port_api",
            "engines_enabled", "country_code", "latitude", "longitude",
            "status", "last_seen_at", "is_active", "created_at", "updated_at",
        ]
        read_only_fields = ["id", "status", "last_seen_at", "created_at", "updated_at"]


class NodeRegisterSerializer(serializers.Serializer):
    """Данные, которые агент присылает при самостоятельной регистрации ноды."""
    address = serializers.CharField(max_length=255)
    agent_port = serializers.IntegerField(required=False)
