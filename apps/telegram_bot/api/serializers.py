"""DRF serializers for telegram_bot."""
from rest_framework import serializers

from apps.telegram_bot.models import TelegramAccount, TelegramLinkCode


class TelegramLinkCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramLinkCode
        fields = ["code", "expires_at"]
        read_only_fields = fields


class TelegramAccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = TelegramAccount
        fields = ["telegram_id", "telegram_username", "linked_at"]
        read_only_fields = fields
