from rest_framework.routers import DefaultRouter

from .views import RoutingRuleViewSet

app_name = "routing"

router = DefaultRouter()
router.register(r"", RoutingRuleViewSet, basename="routingrule")

urlpatterns = router.urls
