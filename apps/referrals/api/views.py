"""DRF views for referrals: свой код, история начислений."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.referrals.models import ReferralReward
from apps.referrals.services import get_or_create_referral_code

from .serializers import ReferralCodeSerializer, ReferralRewardSerializer


class MyReferralInfoView(APIView):
    """Возвращает реферальный код текущего пользователя и историю начислений."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        code = get_or_create_referral_code(request.user)
        rewards = ReferralReward.objects.filter(signup__referrer=request.user).select_related("payment")

        return Response({
            "code": ReferralCodeSerializer(code).data,
            "rewards": ReferralRewardSerializer(rewards, many=True).data,
            "total_earned": sum((r.amount for r in rewards), start=0),
        })
