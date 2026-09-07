from django.contrib import admin

from .models import Subscription


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("client", "default_format", "auto_select_best_server", "created_at")
    list_filter = ("default_format", "auto_select_best_server")
    readonly_fields = ("token", "created_at", "updated_at")
    search_fields = ("client__name", "token")
