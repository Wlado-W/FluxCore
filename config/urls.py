from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework.permissions import IsAdminUser, IsAuthenticated

urlpatterns = [
    path("admin/", admin.site.urls),

    # Переключатель языка (RU/EN)
    path("i18n/", include("django.conf.urls.i18n")),

    # Аутентификация (логин/логаут + 2FA)
    path("accounts/", include("apps.accounts.urls")),

    # Лицензия (активация из интерфейса)
    path("license/", include("apps.licensing.urls")),

    # Панель (дашборд, серверный рендеринг)
    path("", include("apps.core.dashboard_urls")),

    # API
    path("api/agent/", include("apps.core.api.urls")),
    path("api/inbounds/", include("apps.inbounds.api.urls")),
    path("api/outbounds/", include("apps.outbounds.api.urls")),
    path("api/routing/", include("apps.routing.api.urls")),
    path("api/clients/", include("apps.clients.api.urls")),
    path("api/subscriptions/", include("apps.subscriptions.api.urls")),
    path("api/billing/", include("apps.billing.api.urls")),
    path("api/referrals/", include("apps.referrals.api.urls")),
    path("api/telegram/", include("apps.telegram_bot.api.urls")),
    path("api/resellers/", include("apps.resellers.api.urls")),
    path("api/monitoring/", include("apps.monitoring.api.urls")),

    # Личный кабинет клиента
    path("cabinet/", include("apps.client_portal.urls")),

    # Публичные подписки (напр. /sub/<token>/)
    path("sub/", include("apps.subscriptions.urls")),

    # --- OpenAPI 3.0 & Swagger UI ---
    # Полная схема — только для staff-администраторов панели (весь внутренний API).
    path("api/schema/", SpectacularAPIView.as_view(permission_classes=[IsAdminUser]), name="schema"),
    path("api/docs/swagger/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("api/docs/redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),

    # Схема только по эндпоинтам реселлеров — для партнёров с ограниченным
    # доступом, чтобы не показывать им весь внутренний API панели.
    path(
        "api/schema/reseller/",
        SpectacularAPIView.as_view(urlconf="apps.resellers.api.urls", permission_classes=[IsAuthenticated]),
        name="schema-reseller",
    ),
    path("api/docs/reseller/", SpectacularSwaggerView.as_view(url_name="schema-reseller"), name="swagger-ui-reseller"),

    # Схема протокола ноды-агента — публичная (агент/install.sh обращается
    # ДО того, как у него появятся какие-либо учётные данные панели).
    path(
        "api/schema/agent/",
        SpectacularAPIView.as_view(urlconf="apps.core.api.urls", permission_classes=[]),
        name="schema-agent",
    ),
    path("api/docs/agent/", SpectacularSwaggerView.as_view(url_name="schema-agent"), name="swagger-ui-agent"),

    # --- Подключение API приложений FluxCore ---
    path("api/v1/updates/", include("apps.updates.urls")),
    path("api/v1/panel-settings/", include("apps.panel_settings.urls")),
    path("api/v1/backups/", include("apps.backup.urls")),
    path("api/v1/system/", include("apps.core.urls")),
    path("api/v1/panel-settings/branding/", include("apps.panel_settings.api.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
