"""
Сигнал: когда Payment.status меняется на COMPLETED — применяем тариф
к клиенту (fulfillment), начисляем реферальное вознаграждение (если
пользователь был приглашён по реферальной ссылке) и комиссию реселлеру
(если пользователь — субклиент реселлера).
"""
from django.db.models.signals import pre_save
from django.dispatch import receiver

from .models import Payment


@receiver(pre_save, sender=Payment)
def handle_payment_completion(sender, instance: Payment, **kwargs):
    if not instance.pk:
        return  # новый платёж — ещё не может "стать" completed из другого статуса

    try:
        previous = Payment.objects.get(pk=instance.pk)
    except Payment.DoesNotExist:
        return

    became_completed = previous.status != Payment.Status.COMPLETED and instance.status == Payment.Status.COMPLETED
    if not became_completed:
        return

    from .services.fulfillment import fulfill_payment
    fulfill_payment(instance)

    # Реферальное вознаграждение и комиссия реселлера — модули могут быть
    # ещё не реализованы на момент подключения billing, импорт защищён.
    try:
        from apps.referrals.services import reward_referrer_for_payment
        reward_referrer_for_payment(instance)
    except ImportError:
        pass

    try:
        from apps.resellers.services import reward_reseller_for_payment
        reward_reseller_for_payment(instance)
    except ImportError:
        pass
