"""
Базовые настройки Django. dev.py и prod.py импортируют этот модуль
и переопределяют/дополняют нужное.
"""
import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent.parent

load_dotenv(BASE_DIR / ".env")

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "change-me-in-env")
DEBUG = os.environ.get("DJANGO_DEBUG", "False").strip().lower() == "true"

# БАГ (найден при сборке install.sh): раньше здесь стоял хардкод `= []`,
# полностью игнорируя .env — на любом реальном деплое Django отвечал бы
# DisallowedHost на все запросы, каким бы ни был ALLOWED_HOSTS в .env.
_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "").strip()
ALLOWED_HOSTS: list[str] = [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # 3rd party
    "rest_framework",
    "drf_spectacular",
    "django_filters",
    "channels",
    "django_celery_beat",

    # local apps
    "apps.accounts",
    "apps.core",
    "apps.inbounds",
    "apps.outbounds",
    "apps.routing",
    "apps.clients",
    "apps.subscriptions",
    "apps.billing",
    "apps.referrals",
    "apps.resellers",
    "apps.monitoring",
    "apps.notifications",
    "apps.telegram_bot",
    "apps.audit",
    "apps.licensing",
    "apps.panel_settings",
    "apps.client_portal",
    "apps.updates",
    "apps.backup",
]

MIDDLEWARE = [
    "apps.licensing.middleware.LicenseEnforcementMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",  # для мультиязычности
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "apps.audit.middleware.AuditLogMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "apps.panel_settings.context_processors.active_theme",
                "apps.panel_settings.context_processors.branding",
                "apps.licensing.tiers.license_context",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"

AUTH_USER_MODEL = "accounts.User"
LOGIN_URL = "/accounts/login/"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("POSTGRES_DB", "vpn_panel"),
        "USER": os.environ.get("POSTGRES_USER", "admin_vpn"),
        "PASSWORD": os.environ.get("POSTGRES_PASSWORD", ""),
        "HOST": os.environ.get("POSTGRES_HOST", "localhost"),
        "PORT": os.environ.get("POSTGRES_PORT", "5432"),
    }
}

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.environ.get("REDIS_URL", "redis://localhost:6379/0")],
        },
    },
}

CELERY_BROKER_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
CELERY_RESULT_BACKEND = os.environ.get("REDIS_URL", "redis://localhost:6379/1")
CELERY_BEAT_SCHEDULER = "django_celery_beat.schedulers:DatabaseScheduler"

# Периодическая проверка/продление токена лицензии (раз в 12 часов).
# Требует, чтобы django-celery-beat использовал DatabaseScheduler (см. выше);
# сама периодическая задача создаётся через `python manage.py migrate` +
# запись в PeriodicTask (или можно оставить как CELERYBEAT_SCHEDULE ниже,
# если DatabaseScheduler не используется в проде).
CELERY_BEAT_SCHEDULE = {
    "licensing-refresh-token": {
        "task": "apps.licensing.tasks.refresh_license_token",
        "schedule": 12 * 60 * 60,  # 12 часов, в секундах
    },
}

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
    ],
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_FILTER_BACKENDS": [
        "django_filters.rest_framework.DjangoFilterBackend",
    ],
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.ScopedRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "agent": "120/min",
        "public_api": "60/min",
    },
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
}

SPECTACULAR_SETTINGS = {
    "TITLE": "FluxCore API",
    "DESCRIPTION": "API панели оркестрации FluxCore",
    "VERSION": "1.0.0",
    "SERVE_INCLUDE_SCHEMA": False,
}

LANGUAGE_CODE = "ru"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("ru", "Русский"),
    ("en", "English"),
]
LOCALE_PATHS = [BASE_DIR / "locale"]

STATIC_URL = "static/"

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Версия панели, показывается в UI ("О программе") и отправляется на сервер
# лицензий при проверке обновлений (apps.updates).
FLUXCORE_VERSION = os.environ.get("FLUXCORE_VERSION", "1.0.0")

# Каталог для хранения архивов резервных копий (apps.backup).
BACKUP_DIR = os.environ.get("BACKUP_DIR", str(BASE_DIR / "backups"))
