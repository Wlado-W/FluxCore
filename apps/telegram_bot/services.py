"""Сервисные функции привязки Telegram-аккаунта."""
from .models import TelegramAccount, TelegramLinkCode


def create_link_code(user) -> TelegramLinkCode:
    """Создаёт новый код привязки, аннулируя предыдущие неиспользованные коды пользователя."""
    TelegramLinkCode.objects.filter(user=user, is_used=False).update(is_used=True)
    return TelegramLinkCode.objects.create(user=user)


def link_telegram_account(code: str, telegram_id: int, telegram_username: str) -> TelegramAccount | None:
    """
    Проверяет код привязки и создаёт TelegramAccount. Возвращает None,
    если код невалиден/истёк, или если этот Telegram-аккаунт уже привязан
    к другому пользователю.
    """
    try:
        link_code = TelegramLinkCode.objects.select_related("user").get(code=code.upper())
    except TelegramLinkCode.DoesNotExist:
        return None

    if not link_code.is_valid:
        return None

    if TelegramAccount.objects.filter(telegram_id=telegram_id).exclude(user=link_code.user).exists():
        return None

    account, _ = TelegramAccount.objects.update_or_create(
        user=link_code.user,
        defaults={"telegram_id": telegram_id, "telegram_username": telegram_username},
    )
    link_code.is_used = True
    link_code.save(update_fields=["is_used"])

    return account


def get_account_by_telegram_id(telegram_id: int) -> TelegramAccount | None:
    return TelegramAccount.objects.select_related("user").filter(telegram_id=telegram_id).first()
