"""
Абстракция платёжного провайдера — единый интерфейс для разных платёжных
систем (YooKassa, Stripe, CryptoCloud и т.п.), чтобы Payment не зависел
от конкретной интеграции напрямую.

Реальные провайдеры (YooKassaProvider, StripeProvider) — TODO: подключить
SDK и реализовать create_payment/handle_webhook по документации провайдера.
Для разработки и ручного тестирования используется ManualProvider, который
сразу помечает платёж оплаченным (никогда не использовать в проде).
"""
from abc import ABC, abstractmethod

from apps.billing.models import Payment


class PaymentProvider(ABC):
    name: str = "abstract"

    @abstractmethod
    def create_payment(self, payment: Payment) -> str:
        """Инициирует платёж у провайдера, возвращает URL для редиректа пользователя на оплату."""

    @abstractmethod
    def handle_webhook(self, payload: dict) -> Payment | None:
        """Обрабатывает вебхук провайдера, обновляет статус Payment, возвращает его (или None, если не найден)."""


class ManualProvider(PaymentProvider):
    """Провайдер-заглушка для разработки: сразу помечает платёж оплаченным."""
    name = "manual"

    def create_payment(self, payment: Payment) -> str:
        from django.utils import timezone

        payment.status = Payment.Status.COMPLETED
        payment.provider = self.name
        payment.paid_at = timezone.now()
        payment.save(update_fields=["status", "provider", "paid_at"])
        return "/billing/payment-success/"

    def handle_webhook(self, payload: dict) -> Payment | None:
        return None  # у ManualProvider нет реальных вебхуков


class YooKassaProvider(PaymentProvider):
    """TODO: интеграция через yookassa SDK (pip install yookassa)."""
    name = "yookassa"

    def create_payment(self, payment: Payment) -> str:
        raise NotImplementedError("Подключить YooKassa SDK и настроить shop_id/secret_key")

    def handle_webhook(self, payload: dict) -> Payment | None:
        raise NotImplementedError


class StripeProvider(PaymentProvider):
    """TODO: интеграция через stripe SDK (pip install stripe)."""
    name = "stripe"

    def create_payment(self, payment: Payment) -> str:
        raise NotImplementedError("Подключить Stripe SDK и настроить secret key")

    def handle_webhook(self, payload: dict) -> Payment | None:
        raise NotImplementedError


_PROVIDERS = {
    "manual": ManualProvider,
    "yookassa": YooKassaProvider,
    "stripe": StripeProvider,
}


def get_provider(name: str) -> PaymentProvider:
    provider_cls = _PROVIDERS.get(name)
    if provider_cls is None:
        raise ValueError(f"Неизвестный платёжный провайдер: {name}")
    return provider_cls()
