from django import forms


class LicenseActivationForm(forms.Form):
    license_key = forms.CharField(
        label="Лицензионный ключ",
        widget=forms.Textarea(attrs={"class": "fc-input", "rows": 4, "placeholder": "Вставь ключ, полученный от продавца"}),
    )
