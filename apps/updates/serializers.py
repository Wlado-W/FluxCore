from rest_framework import serializers

from .models import SystemPatch, UpdateHistory


class SystemPatchSerializer(serializers.ModelSerializer):
    class Meta:
        model = SystemPatch
        fields = [
            "id", "patch_id", "title", "description", "is_bash",
            "source", "status", "applied_at", "logs", "created_at",
        ]
        read_only_fields = fields


class UpdateHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UpdateHistory
        fields = [
            "id", "from_version", "to_version", "download_url",
            "sha256", "status", "message", "started_at", "finished_at",
        ]
        read_only_fields = fields


class ApplyUpdateRequestSerializer(serializers.Serializer):
    download_url = serializers.URLField()
    sha256 = serializers.RegexField(regex=r"^[0-9a-fA-F]{64}$")
    signature = serializers.CharField()
