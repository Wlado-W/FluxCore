"""Django-формы для кастомных CRUD-страниц панели (не через Django admin)."""
from django import forms

from .models import Node, NodeGroup


class NodeForm(forms.ModelForm):
    engines_enabled = forms.MultipleChoiceField(
        choices=Node.Engine.choices,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        label="Движки",
    )

    class Meta:
        model = Node
        fields = [
            "name", "group", "address", "port_agent", "port_api",
            "engines_enabled", "country_code", "latitude", "longitude", "is_active",
        ]
        labels = {
            "name": "Название",
            "group": "Группа (каскад)",
            "address": "Адрес (IP или домен)",
            "port_agent": "Порт агента",
            "port_api": "Порт API движка",
            "country_code": "Код страны (ISO, напр. NL)",
            "latitude": "Широта",
            "longitude": "Долгота",
            "is_active": "Активна",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "fc-input"}),
            "address": forms.TextInput(attrs={"class": "fc-input"}),
            "port_agent": forms.NumberInput(attrs={"class": "fc-input"}),
            "port_api": forms.NumberInput(attrs={"class": "fc-input"}),
            "country_code": forms.TextInput(attrs={"class": "fc-input", "maxlength": 2}),
            "latitude": forms.NumberInput(attrs={"class": "fc-input", "step": "any"}),
            "longitude": forms.NumberInput(attrs={"class": "fc-input", "step": "any"}),
            "group": forms.Select(attrs={"class": "fc-select"}),
        }
