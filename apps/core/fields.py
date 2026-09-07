"""
Кастомное поле Django, хранящее JSON в зашифрованном виде "at rest".
Прозрачно для остального кода: инстанс модели по-прежнему видит обычный
dict, шифрование/расшифровка происходят на границе БД.

Использование: заменить models.JSONField на EncryptedJSONField для полей
с чувствительными данными (Reality private_key, TLS-сертификаты,
учётные данные исходящих и т.п.).
"""
import json

from django.db import models

from apps.core.services.secrets import decrypt_secret, encrypt_secret


class EncryptedJSONField(models.TextField):
    """Хранит JSON как зашифрованный текст; на уровне Python — обычный dict/list."""

    description = "JSON, зашифрованный at rest"

    def from_db_value(self, value, expression, connection):
        if value is None or value == "":
            return None
        decrypted = decrypt_secret(value)
        return json.loads(decrypted)

    def to_python(self, value):
        if value is None or isinstance(value, (dict, list)):
            return value
        try:
            decrypted = decrypt_secret(value)
            return json.loads(decrypted)
        except (ValueError, json.JSONDecodeError):
            return value

    def get_prep_value(self, value):
        if value is None:
            return None
        return encrypt_secret(json.dumps(value))

    def value_to_string(self, obj):
        return json.dumps(self.value_from_object(obj))
