"""DRF serializers for billing."""
from rest_framework import serializers

from apps.billing.models import Payment, PromoCode, Tariff


class TariffSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tariff
        fields = [
            "id", "name", "description", "price", "currency",
            "duration_days", "traffic_limit_bytes", "max_devices", "is_active",
        ]


class PaymentCreateSerializer(serializers.Serializer):
    """Входные данные для создания платежа: тариф + опционально клиент/промокод/провайдер."""
    tariff_id = serializers.IntegerField()
    client_id = serializers.IntegerField(required=False)
    promo_code = serializers.CharField(required=False, allow_blank=True)
    provider = serializers.ChoiceField(choices=["manual", "yookassa", "stripe"], default="manual")


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = [
            "id", "user", "client", "tariff", "promo_code",
            "amount", "currency", "status", "provider", "external_id",
            "created_at", "paid_at",
        ]
        read_only_fields = fields
