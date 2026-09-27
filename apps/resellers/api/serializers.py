"""DRF serializers for resellers."""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.resellers.models import ResellerCommission, ResellerProfile

User = get_user_model()


class ResellerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerProfile
        fields = ["commission_percent", "is_approved", "created_at"]
        read_only_fields = fields


class ResellerCustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id", "username", "date_joined", "is_active"]
        read_only_fields = fields


class ResellerCustomerCreateSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(write_only=True, min_length=8)


class ResellerCommissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ResellerCommission
        fields = ["id", "payment", "amount", "created_at"]
        read_only_fields = fields
