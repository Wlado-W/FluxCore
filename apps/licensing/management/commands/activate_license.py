"""
Инструмент КЛИЕНТА (self-hosted): активирует полученный от продавца
лицензионный ключ на этой инсталляции панели.

Использование: python manage.py activate_license <ключ>
"""
from django.core.management.base import BaseCommand, CommandError

from apps.licensing.services import LicenseError, activate_license


class Command(BaseCommand):
    help = "Активирует лицензионный ключ на этой инсталляции панели"

    def add_arguments(self, parser):
        parser.add_argument("license_key", type=str)

    def handle(self, *args, **options):
        try:
            license_obj = activate_license(options["license_key"])
        except LicenseError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(
            f"Лицензия активирована: {license_obj.customer_name}, "
            f"лимит нод: {license_obj.max_nodes or 'без ограничения'}, "
            f"срок: {license_obj.expires_at or 'бессрочно'}"
        ))
