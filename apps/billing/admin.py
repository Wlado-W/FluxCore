from django.contrib import admin

from .models import Payment, PromoCode, Tariff


@admin.register(Tariff)
class TariffAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "currency", "duration_days", "traffic_limit_bytes", "is_active")
    list_filter = ("is_active", "currency")
    search_fields = ("name",)


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "discount_type", "discount_value", "used_count", "max_uses", "is_active")
    list_filter = ("discount_type", "is_active")
    search_fields = ("code",)


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "client", "tariff", "amount", "currency", "status", "provider", "created_at")
    list_filter = ("status", "provider", "currency")
    search_fields = ("user__username", "external_id")
    readonly_fields = ("created_at",)
