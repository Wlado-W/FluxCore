"""
Шифрование секретов "at rest" (приватные ключи Reality, сертификаты,
учётные данные исходящих) — с интерфейсом, позволяющим позже подключить
HashiCorp Vault вместо локального шифрования, не меняя вызывающий код.

Backend выбирается через переменную окружения SECRETS_BACKEND=local|vault
(по умолчанию local). Ключ для локального шифрования — FLUXCORE_ENCRYPTION_KEY
(сгенерировать: python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())").
"""
import os
from abc import ABC, abstractmethod

from cryptography.fernet import Fernet, InvalidToken


class SecretsBackend(ABC):
    @abstractmethod
    def encrypt(self, plaintext: str) -> str: ...

    @abstractmethod
    def decrypt(self, ciphertext: str) -> str: ...


class LocalFernetBackend(SecretsBackend):
    """Симметричное шифрование на месте, ключ хранится в переменной окружения."""

    def __init__(self):
        key = os.environ.get("FLUXCORE_ENCRYPTION_KEY")
        if not key:
            raise RuntimeError(
                "FLUXCORE_ENCRYPTION_KEY не задан. Сгенерируй: "
                "python -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
            )
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken as exc:
            raise ValueError("Не удалось расшифровать секрет — неверный ключ или повреждённые данные.") from exc


class VaultBackend(SecretsBackend):
    """
    TODO: интеграция с HashiCorp Vault через hvac (pip install hvac).
    Секреты хранятся в Vault KV-хранилище, панель обращается к нему по
    VAULT_ADDR/VAULT_TOKEN вместо локального шифрования. Полезно при
    кластеризации панели (несколько инстансов, единый источник секретов).
    """

    def encrypt(self, plaintext: str) -> str:
        raise NotImplementedError("Подключить hvac и настроить VAULT_ADDR/VAULT_TOKEN")

    def decrypt(self, ciphertext: str) -> str:
        raise NotImplementedError("Подключить hvac и настроить VAULT_ADDR/VAULT_TOKEN")


_BACKENDS = {"local": LocalFernetBackend, "vault": VaultBackend}
_backend_instance: SecretsBackend | None = None


def get_backend() -> SecretsBackend:
    global _backend_instance
    if _backend_instance is None:
        backend_name = os.environ.get("SECRETS_BACKEND", "local")
        backend_cls = _BACKENDS.get(backend_name)
        if backend_cls is None:
            raise ValueError(f"Неизвестный SECRETS_BACKEND: {backend_name}")
        _backend_instance = backend_cls()
    return _backend_instance


def encrypt_secret(plaintext: str) -> str:
    return get_backend().encrypt(plaintext)


def decrypt_secret(ciphertext: str) -> str:
    return get_backend().decrypt(ciphertext)
