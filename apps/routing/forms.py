"""Django-форма для кастомного CRUD правил маршрутизации (не через Django admin)."""
from django import forms

from .models import RoutingRule


class RoutingRuleForm(forms.ModelForm):
    class Meta:
        model = RoutingRule
        fields = [
            "node", "name", "priority", "match_type", "match_values",
            "target_outbound", "target_balancer_tag", "is_active",
        ]
        labels = {
            "node": "Нода",
            "name": "Название правила",
            "priority": "Приоритет (меньше — выше)",
            "match_type": "Тип условия",
            "match_values": "Значения условия (JSON-список)",
            "target_outbound": "Целевой outbound",
            "target_balancer_tag": "...или тег balancer-группы",
            "is_active": "Активно",
        }
        widgets = {
            "name": forms.TextInput(attrs={"class": "fc-input"}),
            "priority": forms.NumberInput(attrs={"class": "fc-input"}),
            "target_balancer_tag": forms.TextInput(attrs={"class": "fc-input"}),
            "node": forms.Select(attrs={"class": "fc-select"}),
            "match_type": forms.Select(attrs={"class": "fc-select"}),
            "target_outbound": forms.Select(attrs={"class": "fc-select"}),
        }
        help_texts = {
            "match_values": 'Например: ["geosite:netflix", "geosite:youtube"] или ["1.2.3.0/24"]',
            "target_outbound": "Заполни либо это поле, либо тег balancer-группы ниже — не оба сразу.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["match_values"].widget.attrs.update({"class": "fc-input fc-json-input", "rows": 3})
        self.fields["target_outbound"].required = False
        self.fields["target_balancer_tag"].required = False
