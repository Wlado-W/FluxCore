"""DRF views for billing: список тарифов, создание платежа, история платежей."""
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.billing.models import Payment, Tariff
from apps.billing.services.promo import PromoCodeError, apply_promo_code
from apps.billing.services.providers import get_provider
from apps.clients.models import Client

from .serializers import PaymentCreateSerializer, PaymentSerializer, TariffSerializer


class TariffViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tariff.objects.filter(is_active=True)
    serializer_class = TariffSerializer
    permission_classes = [IsAuthenticated]


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """История платежей текущего пользователя."""
    serializer_class = PaymentSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Payment.objects.filter(user=self.request.user).select_related("client", "tariff", "promo_code")


class PaymentCreateView(APIView):
    """Инициирует оплату тарифа: создаёт Payment(pending) и возвращает URL для редиректа на оплату."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PaymentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            tariff = Tariff.objects.get(id=data["tariff_id"], is_active=True)
        except Tariff.DoesNotExist:
            return Response({"detail": "Тариф не найден."}, status=404)

        client = None
        if data.get("client_id"):
            try:
                client = Client.objects.get(id=data["client_id"], owner=request.user)
            except Client.DoesNotExist:
                return Response({"detail": "Клиент не найден."}, status=404)

        amount = tariff.price
        promo = None
        if data.get("promo_code"):
            try:
                amount, promo = apply_promo_code(data["promo_code"], amount)
            except PromoCodeError as exc:
                return Response({"detail": str(exc)}, status=400)

        payment = Payment.objects.create(
            user=request.user, client=client, tariff=tariff, promo_code=promo,
            amount=amount, currency=tariff.currency, status=Payment.Status.PENDING,
        )

        if promo:
            promo.used_count += 1
            promo.save(update_fields=["used_count"])

        provider = get_provider(data["provider"])
        redirect_url = provider.create_payment(payment)

        return Response({"payment_id": payment.id, "redirect_url": redirect_url, "status": payment.status})
