from django.contrib import admin

from .models import TelegramAccount, TelegramLinkCode


@admin.register(TelegramAccount)
class TelegramAccountAdmin(admin.ModelAdmin):
    list_display = ("user", "telegram_id", "telegram_username", "linked_at")
    search_fields = ("user__username", "telegram_username", "telegram_id")


@admin.register(TelegramLinkCode)
class TelegramLinkCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "is_used", "expires_at", "created_at")
    list_filter = ("is_used",)
    readonly_fields = ("code", "created_at")
