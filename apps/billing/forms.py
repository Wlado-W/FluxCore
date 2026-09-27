"""Django-форма для кастомного CRUD тарифов (не через Django admin)."""
from django import forms

from .models import PromoCode, Tariff


class TariffForm(forms.ModelForm):
    class Meta:
        model = Tariff
        fields = [
            "name", "description", "price", "currency",
            "duration_days", "traffic_limit_bytes", "max_devices", "is_active",
        ]
        labels = {
            "name": "Название тарифа",
            "description": "Описание",
            "price": "Цена",
            "currency": "Валюта",
            "duration_days": "Срок действия, дней (пусто = бессрочно)",
            "traffic_limit_bytes": "Лимит трафика, байт (пусто = безлимит)",
            "max_devices": "Лимит устройств (пусто = без ограничения)",
            "is_active": "Тариф активен (доступен для покупки)",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "fc-input"}),
            "description": forms.Textarea(attrs={"class": "fc-input", "rows": 3}),
            "price": forms.NumberInput(attrs={"class": "fc-input", "step": "0.01"}),
            "currency": forms.TextInput(attrs={"class": "fc-input", "maxlength": 3}),
            "duration_days": forms.NumberInput(attrs={"class": "fc-input"}),
            "traffic_limit_bytes": forms.NumberInput(attrs={"class": "fc-input"}),
            "max_devices": forms.NumberInput(attrs={"class": "fc-input"}),
        }


class PromoCodeForm(forms.ModelForm):
    class Meta:
        model = PromoCode
        fields = ["code", "discount_type", "discount_value", "max_uses", "valid_from", "valid_until", "is_active"]
        labels = {
            "code": "Код",
            "discount_type": "Тип скидки",
            "discount_value": "Размер скидки (% или сумма)",
            "max_uses": "Лимит использований (пусто = без лимита)",
            "valid_from": "Действует с",
            "valid_until": "Действует до",
            "is_active": "Активен",
        }
        widgets = {
            "code": forms.TextInput(attrs={"class": "fc-input"}),
            "discount_type": forms.Select(attrs={"class": "fc-select"}),
            "discount_value": forms.NumberInput(attrs={"class": "fc-input", "step": "0.01"}),
            "max_uses": forms.NumberInput(attrs={"class": "fc-input"}),
            "valid_from": forms.DateTimeInput(attrs={"class": "fc-input", "type": "datetime-local"}),
            "valid_until": forms.DateTimeInput(attrs={"class": "fc-input", "type": "datetime-local"}),
        }
