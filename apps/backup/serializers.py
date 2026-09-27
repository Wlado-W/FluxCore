from rest_framework import serializers

from .models import BackupTask


class BackupTaskSerializer(serializers.ModelSerializer):
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, default=None)

    class Meta:
        model = BackupTask
        fields = [
            "id", "file_name", "file_size", "is_encrypted",
            "created_by_username", "status", "error_message", "created_at",
        ]
        read_only_fields = fields


class CreateBackupRequestSerializer(serializers.Serializer):
    # Пароль опционален: без него архив создаётся незашифрованным, но UI
    # должен явно предупреждать об этом (см. ТЗ — шифрование паролем).
    password = serializers.CharField(required=False, allow_blank=True, min_length=8, max_length=128)


class RestoreBackupRequestSerializer(serializers.Serializer):
    password = serializers.CharField(required=False, allow_blank=True, max_length=128)
    confirm = serializers.BooleanField()

    def validate_confirm(self, value):
        if not value:
            raise serializers.ValidationError(
                "Восстановление перезапишет текущую базу данных — подтвердите операцию (confirm=true)."
            )
        return value
