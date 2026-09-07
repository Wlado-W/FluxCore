"""DRF serializers for referrals."""
from rest_framework import serializers

from apps.referrals.models import ReferralCode, ReferralReward


class ReferralCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralCode
        fields = ["code", "reward_percent", "created_at"]
        read_only_fields = fields


class ReferralRewardSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralReward
        fields = ["id", "payment", "amount", "created_at"]
        read_only_fields = fields
