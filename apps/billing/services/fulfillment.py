"""
Применение оплаченного тарифа к клиенту: продление срока действия,
увеличение лимита трафика, увеличение лимита устройств.

Вызывается после того, как Payment.status стал COMPLETED (см.
apps/billing/signals.py).
"""
from datetime import timedelta

from django.utils import timezone

from apps.billing.models import Payment


def fulfill_payment(payment: Payment) -> None:
    """Продлевает/активирует Client согласно купленному тарифу."""
    if payment.status != Payment.Status.COMPLETED:
        return

    client = payment.client
    if client is None:
        return  # платёж без привязки к клиенту (например, пополнение баланса реселлера)

    tariff = payment.tariff

    if tariff.duration_days:
        base_date = client.expires_at if (client.expires_at and client.expires_at > timezone.now()) else timezone.now()
        client.expires_at = base_date + timedelta(days=tariff.duration_days)

    if tariff.traffic_limit_bytes:
        client.traffic_limit_bytes = tariff.traffic_limit_bytes
        client.traffic_used_bytes = 0  # новый тариф — трафик сбрасывается

    if tariff.max_devices:
        client.max_devices = tariff.max_devices

    client.is_active = True
    client.save(update_fields=["expires_at", "traffic_limit_bytes", "traffic_used_bytes", "max_devices", "is_active"])
