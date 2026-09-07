"""
Подпись и проверка лицензионных ключей через Ed25519 (offline-верификация —
не требует постоянной связи с сервером продавца, что подходит для
self-hosted поставки).

Схема: продавец подписывает JSON-payload {customer, max_nodes, issued_at,
expires_at} своим приватным ключом; панель клиента проверяет подпись
встроенным публичным ключом (безопасно "зашить" в код — он не секретный).

Формат лицензионного ключа: base64(payload_json) + "." + base64(signature)
"""
import base64
import json

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey


class LicenseSignatureError(Exception):
    pass


def generate_keypair() -> tuple[str, str]:
    """Генерирует новую пару ключей (только для продавца, один раз). Возвращает (private_pem, public_pem) в base64."""
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    private_bytes = private_key.private_bytes_raw()
    public_bytes = public_key.public_bytes_raw()

    return base64.b64encode(private_bytes).decode(), base64.b64encode(public_bytes).decode()


def sign_license(payload: dict, private_key_b64: str) -> str:
    """Подписывает payload приватным ключом продавца, возвращает готовый лицензионный ключ."""
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(private_key_b64))
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = private_key.sign(payload_bytes)

    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode()
    signature_b64 = base64.urlsafe_b64encode(signature).decode()
    return f"{payload_b64}.{signature_b64}"


def verify_license(license_key: str, public_key_b64: str) -> dict:
    """Проверяет подпись лицензионного ключа, возвращает payload при успехе."""
    try:
        payload_b64, signature_b64 = license_key.split(".")
        payload_bytes = base64.urlsafe_b64decode(payload_b64)
        signature = base64.urlsafe_b64decode(signature_b64)
    except (ValueError, Exception) as exc:
        raise LicenseSignatureError("Неверный формат лицензионного ключа.") from exc

    public_key = Ed25519PublicKey.from_public_bytes(base64.b64decode(public_key_b64))

    try:
        public_key.verify(signature, payload_bytes)
    except InvalidSignature as exc:
        raise LicenseSignatureError("Подпись лицензии недействительна.") from exc

    return json.loads(payload_bytes)
