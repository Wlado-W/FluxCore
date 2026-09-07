"""
Сервисные функции реферальной системы: получить/создать код пользователя,
зарегистрировать приглашённого, начислить вознаграждение за его оплату.
"""
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import transaction

from .models import ReferralCode, ReferralReward, ReferralSignup

User = get_user_model()


def get_or_create_referral_code(user) -> ReferralCode:
    code, _ = ReferralCode.objects.get_or_create(user=user)
    return code


def register_referral_signup(referral_code_str: str, new_user) -> ReferralSignup | None:
    """
    Вызывается при регистрации нового пользователя, если он пришёл по
    реферальной ссылке (?ref=<code>). Возвращает None, если код невалиден
    или пользователь пытается указать сам себя.
    """
    try:
        referral_code = ReferralCode.objects.select_related("user").get(code=referral_code_str)
    except ReferralCode.DoesNotExist:
        return None

    if referral_code.user_id == new_user.id:
        return None

    signup, _ = ReferralSignup.objects.get_or_create(
        referred_user=new_user, defaults={"referrer": referral_code.user}
    )
    return signup


def reward_referrer_for_payment(payment) -> ReferralReward | None:
    """
    Начисляет вознаграждение пригласившему за оплату, совершённую
    приглашённым пользователем. Идемпотентно — повторный вызов для того же
    платежа ничего не сделает (unique_together в ReferralReward).
    """
    try:
        signup = ReferralSignup.objects.select_related("referrer").get(referred_user=payment.user)
    except ReferralSignup.DoesNotExist:
        return None

    if ReferralReward.objects.filter(signup=signup, payment=payment).exists():
        return None

    referral_code = getattr(signup.referrer, "referral_code", None)
    reward_percent = referral_code.reward_percent if referral_code else Decimal("10")
    reward_amount = (payment.amount * reward_percent / Decimal("100")).quantize(Decimal("0.01"))

    with transaction.atomic():
        reward = ReferralReward.objects.create(signup=signup, payment=payment, amount=reward_amount)
        referrer = signup.referrer
        referrer.balance = referrer.balance + reward_amount
        referrer.save(update_fields=["balance"])

    return reward
