"""
Обработчики Telegram-бота (python-telegram-bot v21, async).

Все обращения к Django ORM обёрнуты в sync_to_async, т.к. библиотека
асинхронная, а Django ORM — синхронный.

Запуск: python manage.py run_telegram_bot (см. management/commands/).
"""
from asgiref.sync import sync_to_async
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import Application, CommandHandler, ContextTypes

from apps.billing.models import Payment, Tariff
from apps.billing.services.providers import get_provider
from apps.clients.models import Client
from apps.subscriptions.services.qr import build_subscription_qr_png

from .services import create_link_code, get_account_by_telegram_id, link_telegram_account


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот FluxCore.\n\n"
        "Чтобы привязать аккаунт, получи код на сайте в личном кабинете "
        "(«Привязать Telegram») и отправь мне: /link <код>\n\n"
        "После привязки доступны команды:\n"
        "/balance — баланс\n"
        "/clients — мои VPN-клиенты\n"
        "/subscription <номер> — ссылка и QR подписки\n"
        "/tariffs — доступные тарифы\n"
        "/buy <id тарифа> <номер клиента> — купить/продлить тариф"
    )


async def link_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text("Использование: /link <код>")
        return

    code = context.args[0]
    tg_user = update.effective_user

    account = await sync_to_async(link_telegram_account)(code, tg_user.id, tg_user.username or "")
    if account is None:
        await update.message.reply_text("Код неверен, истёк, или этот Telegram уже привязан к другому аккаунту.")
        return

    await update.message.reply_text(f"Аккаунт {account.user.username} успешно привязан ✅")


async def _require_account(update: Update):
    account = await sync_to_async(get_account_by_telegram_id)(update.effective_user.id)
    if account is None:
        await update.message.reply_text("Сначала привяжи аккаунт: получи код на сайте и отправь /link <код>.")
    return account


async def balance_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = await _require_account(update)
    if account is None:
        return
    await update.message.reply_text(f"Баланс: {account.user.balance} ₽")


async def clients_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = await _require_account(update)
    if account is None:
        return

    clients = await sync_to_async(list)(Client.objects.filter(owner=account.user))
    if not clients:
        await update.message.reply_text("У тебя пока нет VPN-клиентов.")
        return

    lines = []
    for i, client in enumerate(clients, start=1):
        status = "активен" if client.is_active and not client.is_expired else "неактивен"
        lines.append(f"{i}. {client.name} — {status}")
    lines.append("\nПодробности подписки: /subscription <номер>")
    await update.message.reply_text("\n".join(lines))


async def subscription_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = await _require_account(update)
    if account is None:
        return

    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text("Использование: /subscription <номер> (см. /clients)")
        return

    index = int(context.args[0]) - 1
    clients = await sync_to_async(list)(Client.objects.filter(owner=account.user))
    if index < 0 or index >= len(clients):
        await update.message.reply_text("Клиент с таким номером не найден.")
        return

    client = clients[index]
    subscription = await sync_to_async(lambda: getattr(client, "subscription", None))()
    if subscription is None:
        await update.message.reply_text("У этого клиента ещё нет подписки.")
        return

    sub_url = f"https://{context.bot_data.get('panel_domain', 'localhost')}/sub/{subscription.token}/"
    qr_bytes = build_subscription_qr_png(sub_url)

    await update.message.reply_photo(photo=qr_bytes, caption=f"Подписка «{client.name}»:\n{sub_url}")


async def tariffs_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    tariffs = await sync_to_async(list)(Tariff.objects.filter(is_active=True))
    if not tariffs:
        await update.message.reply_text("Пока нет доступных тарифов.")
        return

    lines = [f"{t.id}. {t.name} — {t.price} {t.currency}" for t in tariffs]
    lines.append("\nКупить: /buy <id тарифа> <номер клиента из /clients>")
    await update.message.reply_text("\n".join(lines))


async def buy_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    account = await _require_account(update)
    if account is None:
        return

    if len(context.args) < 2 or not all(a.isdigit() for a in context.args[:2]):
        await update.message.reply_text("Использование: /buy <id тарифа> <номер клиента>")
        return

    tariff_id, client_index = int(context.args[0]), int(context.args[1]) - 1

    def _create_payment():
        try:
            tariff = Tariff.objects.get(id=tariff_id, is_active=True)
        except Tariff.DoesNotExist:
            return None, "Тариф не найден."

        clients = list(Client.objects.filter(owner=account.user))
        if client_index < 0 or client_index >= len(clients):
            return None, "Клиент не найден."

        payment = Payment.objects.create(
            user=account.user, client=clients[client_index], tariff=tariff,
            amount=tariff.price, currency=tariff.currency, status=Payment.Status.PENDING,
        )
        provider = get_provider("manual")  # TODO: заменить на реальный провайдер, когда подключим SDK
        redirect_url = provider.create_payment(payment)
        return (payment, redirect_url), None

    result, error = await sync_to_async(_create_payment)()
    if error:
        await update.message.reply_text(error)
        return

    payment, redirect_url = result
    await update.message.reply_text(
        f"Платёж создан на {payment.amount} {payment.currency}.\nСсылка на оплату: {redirect_url}"
    )


def build_application(token: str, panel_domain: str) -> Application:
    application = Application.builder().token(token).build()
    application.bot_data["panel_domain"] = panel_domain

    application.add_handler(CommandHandler("start", start_handler))
    application.add_handler(CommandHandler("link", link_handler))
    application.add_handler(CommandHandler("balance", balance_handler))
    application.add_handler(CommandHandler("clients", clients_handler))
    application.add_handler(CommandHandler("subscription", subscription_handler))
    application.add_handler(CommandHandler("tariffs", tariffs_handler))
    application.add_handler(CommandHandler("buy", buy_handler))

    return application
