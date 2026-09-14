"""
Сервисные функции лицензирования: активация ключа через удалённый сервер
лицензий продавца (не офлайн-проверка внутри самой панели!), проверка
лимита нод, получение текущего действующего токена.
"""
import os
from datetime import datetime, timezone as dt_timezone

import requests
from django.utils import timezone

from .crypto import LicenseSignatureError, verify_license
from .hardware import get_hardware_fingerprint
from .models import License, RemoteActivationToken


class LicenseError(Exception):
    pass


class LicenseLimitExceeded(LicenseError):
    pass


def _get_public_key() -> str:
    key = os.environ.get("LICENSING_PUBLIC_KEY")
    if not key:
        raise LicenseError("LICENSING_PUBLIC_KEY не задан в .env.")
    return key


def _get_license_server_url() -> str:
    url = os.environ.get("LICENSE_SERVER_URL")
    if not url:
        raise LicenseError("LICENSE_SERVER_URL не задан в .env — панель не знает, куда обращаться за активацией.")
    return url.rstrip("/")


def fetch_remote_token(license_key: str, timeout: int = 10) -> RemoteActivationToken:
    """
    Обращается к серверу лицензий продавца за коротким подписанным
    токеном активации. Бросает LicenseError, если сервер недоступен,
    ключ отозван, или подпись ответа не проходит проверку.
    """
    server_url = _get_license_server_url()
    fingerprint = get_hardware_fingerprint()

    try:
        response = requests.post(
            f"{server_url}/v1/activate",
            json={"license_key": license_key, "hardware_fingerprint": fingerprint},
            timeout=timeout,
        )
    except requests.RequestException as exc:
        raise LicenseError(f"Сервер лицензий недоступен: {exc}") from exc

    if response.status_code != 200:
        detail = response.json().get("detail", "Неизвестная ошибка") if response.content else "Нет ответа"
        raise LicenseError(f"Отказ в активации: {detail}")

    data = response.json()
    token_str = data["token"]

    try:
        payload = verify_license(token_str, _get_public_key())
    except LicenseSignatureError as exc:
        raise LicenseError(f"Подпись токена от сервера лицензий недействительна: {exc}") from exc

    if payload.get("hardware_fingerprint") != fingerprint:
        raise LicenseError("Токен выдан для другого сервера (несовпадение отпечатка железа).")

    issued_at = datetime.fromtimestamp(payload["issued_at"], tz=dt_timezone.utc)
    expires_at = datetime.fromtimestamp(payload["expires_at"], tz=dt_timezone.utc)

    # Храним только один актуальный токен — старые больше не нужны
    RemoteActivationToken.objects.all().delete()
    return RemoteActivationToken.objects.create(
        token=token_str, max_nodes=payload.get("max_nodes"), issued_at=issued_at, expires_at=expires_at,
    )


def activate_license(license_key: str) -> License:
    """Сохраняет ключ и сразу же получает первый токен активации у сервера продавца."""
    fetch_remote_token(license_key)  # бросит LicenseError, если ключ невалиден/отозван
    License.objects.all().delete()  # одна лицензия на инсталляцию
    return License.objects.create(key=license_key)


def get_current_license() -> License | None:
    return License.objects.order_by("-activated_at").first()


def has_valid_remote_token() -> bool:
    """Используется middleware — есть ли действующий, не просроченный токен."""
    token = RemoteActivationToken.objects.order_by("-fetched_at").first()
    if token is None:
        return False
    return token.expires_at > timezone.now()


def refresh_token_if_needed() -> None:
    """
    Вызывается периодической Celery-задачей — продлевает токен заранее,
    пока текущий ещё не истёк, чтобы админ не видел разрывов в работе.
    Если сервер лицензий недоступен — токен просто не обновится и
    доступ заблокируется, когда истечёт текущий (см. middleware).
    """
    license_obj = get_current_license()
    if license_obj is None:
        return
    try:
        fetch_remote_token(license_obj.key)
    except LicenseError:
        pass  # тихо игнорируем — middleware сам заблокирует доступ при истечении


def check_node_limit(current_node_count: int) -> None:
    token = RemoteActivationToken.objects.order_by("-fetched_at").first()
    if token is None or token.expires_at <= timezone.now():
        raise LicenseLimitExceeded("Нет действующего токена активации. Зайди в /license/ для активации.")
    if token.max_nodes is not None and current_node_count >= token.max_nodes:
        raise LicenseLimitExceeded(f"Достигнут лимит нод по лицензии ({token.max_nodes}).")
