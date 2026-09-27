import os

from .base import *  # noqa

DEBUG = False
# ALLOWED_HOSTS уже разобран из .env в base.py (переменная ALLOWED_HOSTS) —
# раньше здесь было повторное чтение из ДРУГОЙ переменной (DJANGO_ALLOWED_HOSTS),
# что было вторым, расходящимся источником истины для одного и того же значения.

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
