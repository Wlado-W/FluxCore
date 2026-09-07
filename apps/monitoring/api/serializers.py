"""DRF serializers for monitoring analytics."""
from rest_framework import serializers

from apps.clients.models import Client


class TopClientSerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Client
        fields = ["id", "name", "owner_username", "traffic_used_bytes", "traffic_limit_bytes"]


class HeatmapEntrySerializer(serializers.Serializer):
    weekday = serializers.IntegerField()
    hour = serializers.IntegerField()
    avg_cpu = serializers.FloatField()
    avg_ram = serializers.FloatField()


class ForecastSerializer(serializers.Serializer):
    field = serializers.CharField()
    current_value = serializers.FloatField(allow_null=True)
    slope_per_day = serializers.FloatField(allow_null=True)
    days_until_threshold = serializers.FloatField(allow_null=True)
    threshold = serializers.FloatField(required=False)
    message = serializers.CharField(required=False)
