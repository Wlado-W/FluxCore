"""Django-форма для кастомного CRUD инбаундов (не через Django admin)."""
from django import forms

from .models import Inbound


class InboundForm(forms.ModelForm):
    class Meta:
        model = Inbound
        fields = [
            "node", "engine", "tag", "protocol", "listen", "port",
            "transport", "transport_settings",
            "security", "security_settings",
            "sniffing_enabled", "sniffing_dest_override",
            "tcp_mask_enabled", "tcp_mask_settings",
            "sockopt", "proxy_protocol_enabled", "http_obfuscation_settings",
            "is_active",
        ]
        labels = {
            "node": "Нода",
            "engine": "Движок",
            "tag": "Тег (уникальное имя в конфиге)",
            "protocol": "Протокол",
            "listen": "Адрес прослушивания",
            "port": "Порт",
            "transport": "Транспорт",
            "transport_settings": "Настройки транспорта (JSON)",
            "security": "Безопасность",
            "security_settings": "Настройки TLS/Reality (JSON)",
            "sniffing_enabled": "Sniffing включён",
            "sniffing_dest_override": "Sniffing: destOverride (JSON-список)",
            "tcp_mask_enabled": "TCP mask включён",
            "tcp_mask_settings": "Настройки TCP mask (JSON)",
            "sockopt": "sockopt (JSON)",
            "proxy_protocol_enabled": "Proxy protocol включён",
            "http_obfuscation_settings": "HTTP-обфускация (JSON)",
            "is_active": "Активен",
        }
        widgets = {
            "tag": forms.TextInput(attrs={"class": "fc-input"}),
            "listen": forms.TextInput(attrs={"class": "fc-input"}),
            "port": forms.NumberInput(attrs={"class": "fc-input"}),
            "node": forms.Select(attrs={"class": "fc-select"}),
            "engine": forms.Select(attrs={"class": "fc-select"}),
            "protocol": forms.Select(attrs={"class": "fc-select"}),
            "transport": forms.Select(attrs={"class": "fc-select"}),
            "security": forms.Select(attrs={"class": "fc-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # JSON-поля рендерятся как forms.JSONField (см. apps.core.fields.EncryptedJSONField.formfield
        # и обычный JSONField для sniffing_dest_override/sockopt) — добавим единый класс textarea.
        json_fields = [
            "transport_settings", "security_settings", "sniffing_dest_override",
            "tcp_mask_settings", "sockopt", "http_obfuscation_settings",
        ]
        for name in json_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({"class": "fc-input fc-json-input", "rows": 3})
                self.fields[name].required = False
