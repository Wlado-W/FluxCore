from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import PaymentCreateView, PaymentViewSet, TariffViewSet

app_name = "billing"

router = DefaultRouter()
router.register(r"tariffs", TariffViewSet, basename="tariff")
router.register(r"payments", PaymentViewSet, basename="payment")

urlpatterns = [
    path("payments/create/", PaymentCreateView.as_view(), name="payment-create"),
] + router.urls
