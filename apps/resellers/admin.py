from django.contrib import admin

from .models import ResellerCommission, ResellerProfile


@admin.register(ResellerProfile)
class ResellerProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "commission_percent", "is_approved", "created_at")
    list_filter = ("is_approved",)
    search_fields = ("user__username",)


@admin.register(ResellerCommission)
class ResellerCommissionAdmin(admin.ModelAdmin):
    list_display = ("reseller", "payment", "amount", "created_at")
    readonly_fields = ("reseller", "payment", "amount", "created_at")
    search_fields = ("reseller__username",)

    def has_add_permission(self, request):
        return False
