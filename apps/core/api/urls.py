from django.urls import path
from rest_framework.routers import DefaultRouter

from .map_views import NodeMapView
from .views import NodeRegisterView, NodeViewSet

app_name = "core"

router = DefaultRouter()
router.register(r"nodes", NodeViewSet, basename="node")

urlpatterns = [
    path("nodes/register/", NodeRegisterView.as_view(), name="node-register"),
    path("nodes/map/", NodeMapView.as_view(), name="node-map"),
] + router.urls
