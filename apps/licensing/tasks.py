"""Периодическая задача (Celery Beat): продлевает токен активации, пока он ещё не истёк."""
from celery import shared_task

from .services import refresh_token_if_needed


@shared_task
def refresh_license_token():
    refresh_token_if_needed()
