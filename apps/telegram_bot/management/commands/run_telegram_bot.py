"""
Запуск Telegram-бота в режиме long polling — удобно для разработки.
Для прода рекомендуется перейти на webhook (Application.run_webhook),
особенно при масштабировании панели на несколько инстансов.

Использование: python manage.py run_telegram_bot
Требует переменную окружения TELEGRAM_BOT_TOKEN (см. .env).
"""
import os

from django.core.management.base import BaseCommand, CommandError

from apps.telegram_bot.bot import build_application


class Command(BaseCommand):
    help = "Запускает Telegram-бота FluxCore в режиме polling"

    def handle(self, *args, **options):
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise CommandError("Переменная окружения TELEGRAM_BOT_TOKEN не задана (см. .env)")

        panel_domain = os.environ.get("PANEL_DOMAIN", "localhost:8000")

        self.stdout.write(self.style.SUCCESS("Запуск Telegram-бота FluxCore (polling)..."))
        application = build_application(token, panel_domain)
        application.run_polling()
