"""Django-форма для кастомного CRUD реселлерских профилей (не через Django admin)."""
from django import forms

from .models import ResellerProfile


class ResellerProfileForm(forms.ModelForm):
    class Meta:
        model = ResellerProfile
        fields = ["user", "commission_percent", "is_approved"]
        labels = {
            "user": "Пользователь (роль: reseller)",
            "commission_percent": "Процент комиссии",
            "is_approved": "Одобрен (может создавать субклиентов)",
        }
        widgets = {
            "user": forms.Select(attrs={"class": "fc-select"}),
            "commission_percent": forms.NumberInput(attrs={"class": "fc-input", "step": "0.01"}),
        }
