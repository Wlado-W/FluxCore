from django.urls import path

from .views import MyReferralInfoView

app_name = "referrals"

urlpatterns = [
    path("me/", MyReferralInfoView.as_view(), name="my-referral-info"),
]
