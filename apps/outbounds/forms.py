"""Django-форма для кастомного CRUD исходящих (не через Django admin)."""
from django import forms

from .models import Outbound


class OutboundForm(forms.ModelForm):
    class Meta:
        model = Outbound
        fields = [
            "node", "engine", "tag", "protocol",
            "target_node", "target_inbound_tag",
            "settings", "stream_settings", "sockopt",
            "balancer_tag", "is_active",
        ]
        labels = {
            "node": "Нода",
            "engine": "Движок",
            "tag": "Тег (уникальное имя в конфиге)",
            "protocol": "Протокол",
            "target_node": "Целевая нода (для каскада)",
            "target_inbound_tag": "Тег inbound'а на целевой ноде",
            "settings": "Настройки (JSON): servers, address, port, credentials",
            "stream_settings": "TLS/Reality/transport для исходящего (JSON)",
            "sockopt": "sockopt (JSON)",
            "balancer_tag": "Тег balancer-группы (для failover)",
            "is_active": "Активен",
        }
        widgets = {
            "tag": forms.TextInput(attrs={"class": "fc-input"}),
            "target_inbound_tag": forms.TextInput(attrs={"class": "fc-input"}),
            "balancer_tag": forms.TextInput(attrs={"class": "fc-input"}),
            "node": forms.Select(attrs={"class": "fc-select"}),
            "engine": forms.Select(attrs={"class": "fc-select"}),
            "protocol": forms.Select(attrs={"class": "fc-select"}),
            "target_node": forms.Select(attrs={"class": "fc-select"}),
        }
        help_texts = {
            "target_node": "Заполни, если этот outbound ведёт на следующую ноду в цепочке (каскадирование).",
            "balancer_tag": "Outbound'ы с одинаковым тегом объединяются в группу с авто-failover.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        json_fields = ["settings", "stream_settings", "sockopt"]
        for name in json_fields:
            if name in self.fields:
                self.fields[name].widget.attrs.update({"class": "fc-input fc-json-input", "rows": 3})
                self.fields[name].required = False
