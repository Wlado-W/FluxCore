"""Django-форма для кастомного CRUD клиентов (не через Django admin)."""
from django import forms

from .models import Client, ClientGroup


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = [
            "owner", "group", "name", "password",
            "traffic_limit_bytes", "traffic_used_bytes", "traffic_reset_day",
            "expires_at", "max_devices", "is_active", "is_trial",
            "wg_public_key", "wg_private_key", "wg_allowed_ips",
        ]
        labels = {
            "owner": "Владелец (пользователь)",
            "group": "Группа клиентов",
            "name": "Имя клиента",
            "password": "Пароль (для trojan/shadowsocks/mtproto)",
            "traffic_limit_bytes": "Лимит трафика, байт (пусто = безлимит)",
            "traffic_used_bytes": "Использовано трафика, байт",
            "traffic_reset_day": "День месяца для сброса трафика",
            "expires_at": "Истекает",
            "max_devices": "Лимит устройств (пусто = без ограничения)",
            "is_active": "Активен",
            "is_trial": "Пробный период",
            "wg_public_key": "WireGuard: публичный ключ",
            "wg_private_key": "WireGuard: приватный ключ",
            "wg_allowed_ips": "WireGuard: выделенный IP (напр. 10.0.0.2/32)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "fc-input"}),
            "password": forms.TextInput(attrs={"class": "fc-input"}),
            "traffic_limit_bytes": forms.NumberInput(attrs={"class": "fc-input"}),
            "traffic_used_bytes": forms.NumberInput(attrs={"class": "fc-input"}),
            "traffic_reset_day": forms.NumberInput(attrs={"class": "fc-input", "min": 1, "max": 28}),
            "expires_at": forms.DateTimeInput(attrs={"class": "fc-input", "type": "datetime-local"}),
            "max_devices": forms.NumberInput(attrs={"class": "fc-input"}),
            "wg_public_key": forms.TextInput(attrs={"class": "fc-input"}),
            "wg_private_key": forms.TextInput(attrs={"class": "fc-input"}),
            "wg_allowed_ips": forms.TextInput(attrs={"class": "fc-input"}),
            "owner": forms.Select(attrs={"class": "fc-select"}),
            "group": forms.Select(attrs={"class": "fc-select"}),
        }
        help_texts = {
            "wg_public_key": "Заполняется только для WireGuard-клиентов.",
        }


class ClientGroupForm(forms.ModelForm):
    class Meta:
        model = ClientGroup
        fields = ["name", "description", "inbounds"]
        labels = {
            "name": "Название группы",
            "description": "Описание",
            "inbounds": "Inbound'ы, доступные этой группе",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "fc-input"}),
            "description": forms.Textarea(attrs={"class": "fc-input", "rows": 3}),
            "inbounds": forms.CheckboxSelectMultiple,
        }
