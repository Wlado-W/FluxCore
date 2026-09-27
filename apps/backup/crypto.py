"""
Шифрование файла бэкапа паролем администратора (см. ТЗ блок 5 — скачиваемый
архив должен быть с шифрованием паролем).

Формат: PBKDF2-HMAC-SHA256(390k итераций, случайная соль 16 байт) → ключ →
Fernet (AES-128-CBC + HMAC, аутентифицированное шифрование) поверх сырых
байт исходного .tar.gz. Пароль НИГДЕ не сохраняется — только у админа,
восстановить архив без пароля невозможно (это фича, не баг: цель — чтобы
скачанный бэкап с базой/секретами нод был бесполезен при утечке).

Не используем ZIP-шифрование (ZipCrypto) — оно криптографически слабое
(известный plaintext-attack) и AES-zip потребовал бы отдельную библиотеку
(pyzipper), которой нет в зависимостях проекта.
"""
import os

from cryptography.fernet import Fernet, InvalidToken
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

PBKDF2_ITERATIONS = 390_000
SALT_SIZE = 16
CHUNK_SIZE = 1024 * 1024  # 1 MB


class BackupCryptoError(Exception):
    pass


def _derive_key(password: str, salt: bytes) -> bytes:
    import base64

    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=PBKDF2_ITERATIONS)
    return base64.urlsafe_b64encode(kdf.derive(password.encode("utf-8")))


def encrypt_file(input_path: str, output_path: str, password: str) -> None:
    """
    Шифрует input_path целиком в output_path: [16 байт соли][Fernet-токен].
    Примечание: Fernet требует весь payload в памяти — для очень больших БД
    (десятки ГБ) стоит перейти на потоковый AES-GCM, но для типичного
    размера дампа панели этого достаточно и проще в поддержке.
    """
    salt = os.urandom(SALT_SIZE)
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    with open(input_path, "rb") as f:
        plaintext = f.read()

    token = fernet.encrypt(plaintext)

    with open(output_path, "wb") as f:
        f.write(salt)
        f.write(token)


def decrypt_file(input_path: str, output_path: str, password: str) -> None:
    with open(input_path, "rb") as f:
        raw = f.read()

    if len(raw) <= SALT_SIZE:
        raise BackupCryptoError("Файл бэкапа повреждён или не является зашифрованным архивом.")

    salt, token = raw[:SALT_SIZE], raw[SALT_SIZE:]
    key = _derive_key(password, salt)
    fernet = Fernet(key)

    try:
        plaintext = fernet.decrypt(token)
    except InvalidToken as exc:
        raise BackupCryptoError("Неверный пароль или файл бэкапа повреждён.") from exc

    with open(output_path, "wb") as f:
        f.write(plaintext)
