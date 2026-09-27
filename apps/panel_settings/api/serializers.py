from rest_framework import serializers

from ..models import SystemBranding


class SystemBrandingSerializer(serializers.ModelSerializer):
    logo_url = serializers.SerializerMethodField()
    favicon_url = serializers.SerializerMethodField()

    class Meta:
        model = SystemBranding
        fields = [
            "app_name", "logo", "logo_url", "favicon", "favicon_url", "custom_css",
            "ad_enabled", "ad_title", "ad_content", "ad_link",
        ]
        extra_kwargs = {
            "logo": {"write_only": True, "required": False},
            "favicon": {"write_only": True, "required": False},
        }

    def get_logo_url(self, obj):
        request = self.context.get("request")
        if not obj.logo:
            return None
        return request.build_absolute_uri(obj.logo.url) if request else obj.logo.url

    def get_favicon_url(self, obj):
        request = self.context.get("request")
        if not obj.favicon:
            return None
        return request.build_absolute_uri(obj.favicon.url) if request else obj.favicon.url
