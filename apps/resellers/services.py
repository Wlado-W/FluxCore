"""Сервисные функции реселлерской системы."""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import ResellerCommission, ResellerProfile

User = get_user_model()


class ResellerError(Exception):
    pass


def create_customer(reseller: User, username: str, password: str) -> User:
    """Создаёт нового субклиента под реселлером."""
    if reseller.role != User.Role.RESELLER:
        raise ResellerError("Создавать субклиентов может только пользователь с ролью reseller.")

    profile = ResellerProfile.objects.filter(user=reseller).first()
    if profile is None or not profile.is_approved:
        raise ResellerError("Реселлер ещё не одобрен администратором.")

    if User.objects.filter(username=username).exists():
        raise ResellerError("Пользователь с таким именем уже существует.")

    customer = User.objects.create_user(
        username=username, password=password, role=User.Role.CLIENT, parent_reseller=reseller,
    )
    return customer


def get_reseller_customers(reseller: User):
    return User.objects.filter(parent_reseller=reseller, role=User.Role.CLIENT)


def reward_reseller_for_payment(payment) -> ResellerCommission | None:
    """
    Начисляет комиссию реселлеру, если платёж совершил один из его
    субклиентов. Идемпотентно — повторный вызов для того же платежа
    ничего не сделает (unique_together в ResellerCommission).
    """
    customer = payment.user
    reseller = customer.parent_reseller
    if reseller is None:
        return None

    if ResellerCommission.objects.filter(reseller=reseller, payment=payment).exists():
        return None

    profile = ResellerProfile.objects.filter(user=reseller).first()
    commission_percent = profile.commission_percent if profile else Decimal("15")
    commission_amount = (payment.amount * commission_percent / Decimal("100")).quantize(Decimal("0.01"))

    with transaction.atomic():
        commission = ResellerCommission.objects.create(
            reseller=reseller, payment=payment, amount=commission_amount
        )
        reseller.balance = reseller.balance + commission_amount
        reseller.save(update_fields=["balance"])

    return commission
