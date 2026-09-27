"""DRF views for telegram_bot: генерация кода привязки, статус привязки текущего пользователя."""
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.telegram_bot.models import TelegramAccount
from apps.telegram_bot.services import create_link_code

from .serializers import TelegramAccountSerializer, TelegramLinkCodeSerializer


class TelegramLinkCodeCreateView(APIView):
    """Генерирует новый код привязки для текущего пользователя (действует 10 минут)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        link_code = create_link_code(request.user)
        return Response(TelegramLinkCodeSerializer(link_code).data)


class TelegramAccountStatusView(APIView):
    """Показывает, привязан ли Telegram у текущего пользователя."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        account = TelegramAccount.objects.filter(user=request.user).first()
        if account is None:
            return Response({"linked": False})
        return Response({"linked": True, **TelegramAccountSerializer(account).data})
