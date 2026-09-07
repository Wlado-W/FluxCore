from django.urls import path

from . import views

app_name = "subscriptions_public"

urlpatterns = [
    path("<str:token>/", views.subscription_view, name="subscription"),
    path("<str:token>/qr/", views.subscription_qr_view, name="subscription_qr"),
    path("<str:token>/apps/", views.subscription_deep_links_view, name="subscription_deep_links"),
]
