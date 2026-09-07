from django.urls import path

from .views import TelegramAccountStatusView, TelegramLinkCodeCreateView

app_name = "telegram_bot"

urlpatterns = [
    path("link-code/", TelegramLinkCodeCreateView.as_view(), name="link-code-create"),
    path("status/", TelegramAccountStatusView.as_view(), name="status"),
]
