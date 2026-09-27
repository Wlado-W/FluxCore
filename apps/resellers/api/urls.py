from django.urls import path

from .views import ResellerCommissionsView, ResellerCustomersView, ResellerMeView

app_name = "resellers"

urlpatterns = [
    path("me/", ResellerMeView.as_view(), name="me"),
    path("customers/", ResellerCustomersView.as_view(), name="customers"),
    path("commissions/", ResellerCommissionsView.as_view(), name="commissions"),
]
