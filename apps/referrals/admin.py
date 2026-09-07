from django.contrib import admin

from .models import ReferralCode, ReferralReward, ReferralSignup


@admin.register(ReferralCode)
class ReferralCodeAdmin(admin.ModelAdmin):
    list_display = ("user", "code", "reward_percent", "created_at")
    search_fields = ("user__username", "code")
    readonly_fields = ("code", "created_at")


@admin.register(ReferralSignup)
class ReferralSignupAdmin(admin.ModelAdmin):
    list_display = ("referrer", "referred_user", "created_at")
    search_fields = ("referrer__username", "referred_user__username")


@admin.register(ReferralReward)
class ReferralRewardAdmin(admin.ModelAdmin):
    list_display = ("signup", "payment", "amount", "created_at")
    readonly_fields = ("signup", "payment", "amount", "created_at")

    def has_add_permission(self, request):
        return False
