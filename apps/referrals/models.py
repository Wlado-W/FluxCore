"""
referrals app — реферальная система: у каждого пользователя есть свой
реферальный код, по которому регистрируются новые пользователи; когда
приглашённый совершает оплату, пригласивший получает вознаграждение
(начисляется на User.balance).
"""
import uuid

from django.conf import settings
from django.db import models

def generate_referral_code() -> str:
    """Именованная функция вместо lambda"""
    return uuid.uuid4().hex[:8]

class ReferralCode(models.Model):
    """Персональный реферальный код пользователя (генерируется один раз)."""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referral_code"
    )
    code = models.CharField(max_length=16, unique=True, default=generate_referral_code)
    reward_percent = models.DecimalField(
        max_digits=5, decimal_places=2, default=10,
        help_text="Процент от суммы оплаты приглашённого, начисляемый пригласившему",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username}: {self.code}"


class ReferralSignup(models.Model):
    """Связь пригласивший → приглашённый, фиксируется при регистрации по коду."""
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referred_signups"
    )
    referred_user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="referred_by"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.referrer.username} → {self.referred_user.username}"


class ReferralReward(models.Model):
    """Начисление за оплату, совершённую приглашённым пользователем."""
    signup = models.ForeignKey(ReferralSignup, on_delete=models.CASCADE, related_name="rewards")
    payment = models.ForeignKey("billing.Payment", on_delete=models.CASCADE, related_name="referral_rewards")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = [("signup", "payment")]  # защита от повторного начисления за один платёж

    def __str__(self):
        return f"{self.signup.referrer.username}: +{self.amount} (за платёж #{self.payment_id})"
