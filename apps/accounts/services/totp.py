"""
Хелперы для двухфакторной аутентификации (TOTP) через pyotp.

Секрет хранится в User.totp_secret, флаг User.is_2fa_enabled включается
только после того, как пользователь успешно ввёл код при настройке
(чтобы не заблокировать вход, если он неправильно отсканировал QR).
"""
import pyotp

ISSUER_NAME = "FluxCore"


def generate_totp_secret() -> str:
    """Генерирует новый случайный base32-секрет для пользователя."""
    return pyotp.random_base32()


def get_provisioning_uri(user, secret: str) -> str:
    """
    URI вида otpauth://totp/... для генерации QR-кода — приложение-
    аутентификатор (Google Authenticator, Aegis и т.п.) сканирует его.
    """
    return pyotp.totp.TOTP(secret).provisioning_uri(
        name=user.username, issuer_name=ISSUER_NAME
    )


def verify_totp_code(secret: str, code: str) -> bool:
    """Проверяет 6-значный код с допуском в 1 временное окно (±30 сек)."""
    if not secret or not code:
        return False
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
