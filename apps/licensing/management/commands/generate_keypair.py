"""
Инструмент ПРОДАВЦА (не для self-hosted клиентов!): генерирует пару
ключей Ed25519 один раз. Приватный ключ храни в секрете (используется для
подписи лицензий через generate_license), публичный — раздаётся клиентам
в переменную окружения LICENSING_PUBLIC_KEY.
"""
from django.core.management.base import BaseCommand

from apps.licensing.crypto import generate_keypair


class Command(BaseCommand):
    help = "Генерирует пару ключей для подписи лицензий (только для продавца, один раз)"

    def handle(self, *args, **options):
        private_key, public_key = generate_keypair()
        self.stdout.write(self.style.WARNING("⚠️  Приватный ключ храни в секрете, никогда не публикуй!\n"))
        self.stdout.write(f"LICENSING_PRIVATE_KEY={private_key}")
        self.stdout.write(f"LICENSING_PUBLIC_KEY={public_key}")
