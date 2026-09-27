"""DRF views for resellers: профиль, субклиенты, комиссии."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.resellers.models import ResellerCommission, ResellerProfile
from apps.resellers.services import ResellerError, create_customer, get_reseller_customers

from .serializers import (
    ResellerCommissionSerializer,
    ResellerCustomerCreateSerializer,
    ResellerCustomerSerializer,
    ResellerProfileSerializer,
)


class ResellerMeView(APIView):
    """Профиль реселлера + баланс (баланс — уже поле User, см. accounts)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = ResellerProfile.objects.filter(user=request.user).first()
        if profile is None:
            return Response({"detail": "У тебя нет реселлерского профиля."}, status=404)
        return Response({
            "profile": ResellerProfileSerializer(profile).data,
            "balance": request.user.balance,
        })


class ResellerCustomersView(APIView):
    """Список субклиентов реселлера + создание нового."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        customers = get_reseller_customers(request.user)
        return Response(ResellerCustomerSerializer(customers, many=True).data)

    def post(self, request):
        serializer = ResellerCustomerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            customer = create_customer(
                request.user, serializer.validated_data["username"], serializer.validated_data["password"]
            )
        except ResellerError as exc:
            return Response({"detail": str(exc)}, status=400)

        return Response(ResellerCustomerSerializer(customer).data, status=201)


class ResellerCommissionsView(APIView):
    """История начислений комиссии реселлеру."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        commissions = ResellerCommission.objects.filter(reseller=request.user).select_related("payment")
        return Response({
            "commissions": ResellerCommissionSerializer(commissions, many=True).data,
            "total_earned": sum((c.amount for c in commissions), start=0),
        })
