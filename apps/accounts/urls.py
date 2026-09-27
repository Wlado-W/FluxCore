from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("login/", views.login_view, name="login"),
    path("login/verify/", views.login_verify_view, name="login_verify"),
    path("logout/", views.logout_view, name="logout"),
    path("2fa/setup/", views.setup_2fa_view, name="setup_2fa"),
    path("2fa/setup/qr.png", views.setup_2fa_qr_view, name="setup_2fa_qr"),
    path("2fa/disable/", views.disable_2fa_view, name="disable_2fa"),
]
