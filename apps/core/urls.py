from django.urls import path
from .api.views import AboutSystemView, EULAView

app_name = "core"

urlpatterns = [
    path("about/", AboutSystemView.as_view(), name="about"),
    path("eula/", EULAView.as_view(), name="eula"),
]
