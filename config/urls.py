from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # TODO: path("", include("apps.core.dashboard_urls")) — дашборд панели (серверный рендеринг)

    # API
    path("api/agent/", include("apps.core.api.urls")),
    path("api/inbounds/", include("apps.inbounds.api.urls")),
    path("api/outbounds/", include("apps.outbounds.api.urls")),
    path("api/routing/", include("apps.routing.api.urls")),
    path("api/clients/", include("apps.clients.api.urls")),
    path("api/subscriptions/", include("apps.subscriptions.api.urls")),
    path("api/billing/", include("apps.billing.api.urls")),
    path("api/resellers/", include("apps.resellers.api.urls")),
    path("api/monitoring/", include("apps.monitoring.api.urls")),

    # Личный кабинет клиента
    path("cabinet/", include("apps.client_portal.urls")),

    # Публичные подписки (напр. /sub/<token>/)
    path("sub/", include("apps.subscriptions.urls")),
]
