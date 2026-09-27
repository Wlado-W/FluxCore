"""
Подпись короткоживущих токенов активации тем же Ed25519-ключом, что и
основные лицензии (см. apps/licensing/crypto.py в панели). Приватный
ключ хранится ТОЛЬКО здесь, на сервере лицензий, никогда не покидает его.
"""
import base64
import json
import os

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

PRIVATE_KEY_B64 = os.environ["LICENSING_PRIVATE_KEY"]  # обязателен, без него сервер не запустится


def sign_token(payload: dict) -> str:
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(PRIVATE_KEY_B64))
    payload_bytes = json.dumps(payload, sort_keys=True).encode()
    signature = private_key.sign(payload_bytes)

    payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode()
    signature_b64 = base64.urlsafe_b64encode(signature).decode()
    return f"{payload_b64}.{signature_b64}"


def sign_bytes(data: bytes) -> str:
    """
    Подписывает произвольные байты (sha256-дайджест релиза, текст патч-скрипта)
    тем же приватным ключом продавца. Используется publish_release.py при
    публикации обновления/патча, чтобы панель клиента могла проверить
    подлинность перед выполнением (см. apps/licensing/crypto.py:verify_bytes
    на стороне панели).
    """
    private_key = Ed25519PrivateKey.from_private_bytes(base64.b64decode(PRIVATE_KEY_B64))
    signature = private_key.sign(data)
    return base64.urlsafe_b64encode(signature).decode()
