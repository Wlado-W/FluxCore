from django.urls import path

from .views import BrandingSettingsView

app_name = "panel_settings_api"

urlpatterns = [
    path("", BrandingSettingsView.as_view(), name="branding"),
]
