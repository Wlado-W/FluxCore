from rest_framework.routers import DefaultRouter

from .views import OutboundViewSet

app_name = "outbounds"

router = DefaultRouter()
router.register(r"", OutboundViewSet, basename="outbound")

urlpatterns = router.urls
