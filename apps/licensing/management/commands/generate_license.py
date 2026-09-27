"""
Инструмент ПРОДАВЦА: генерирует подписанный лицензионный ключ для клиента.

Использование:
    python manage.py generate_license --customer "ООО Ромашка" --max-nodes 5 --days 365
"""
import os
from datetime import timedelta

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from apps.licensing.crypto import sign_license


class Command(BaseCommand):
    help = "Генерирует подписанный лицензионный ключ для клиента (инструмент продавца)"

    def add_arguments(self, parser):
        parser.add_argument("--customer", required=True, help="Имя клиента")
        parser.add_argument("--max-nodes", type=int, default=None, help="Лимит нод (не задавать = без лимита)")
        parser.add_argument("--days", type=int, default=None, help="Срок действия в днях (не задавать = бессрочно)")

    def handle(self, *args, **options):
        private_key = os.environ.get("LICENSING_PRIVATE_KEY")
        if not private_key:
            raise CommandError(
                "LICENSING_PRIVATE_KEY не задан. Сначала: python manage.py generate_keypair"
            )

        now = timezone.now()
        payload = {
            "customer": options["customer"],
            "max_nodes": options["max_nodes"],
            "issued_at": now.isoformat(),
            "expires_at": (now + timedelta(days=options["days"])).isoformat() if options["days"] else None,
        }

        license_key = sign_license(payload, private_key)
        self.stdout.write(self.style.SUCCESS("Лицензионный ключ сгенерирован:\n"))
        self.stdout.write(license_key)
