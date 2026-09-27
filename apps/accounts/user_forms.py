"""Django-формы для кастомного CRUD пользователей (не через Django admin)."""
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

User = get_user_model()


class UserCreateForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ("email", "role", "parent_reseller")
        labels = {"role": "Роль", "parent_reseller": "Реселлер-родитель (если это субклиент)"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for name in ("username", "email"):
            self.fields[name].widget.attrs.update({"class": "fc-input"})
        for name in ("password1", "password2"):
            self.fields[name].widget.attrs.update({"class": "fc-input"})
        self.fields["role"].widget.attrs.update({"class": "fc-select"})
        self.fields["parent_reseller"].widget.attrs.update({"class": "fc-select"})
        self.fields["parent_reseller"].required = False


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username", "email", "role", "balance", "parent_reseller", "is_active"]
        labels = {
            "username": "Логин",
            "email": "Email",
            "role": "Роль",
            "balance": "Баланс",
            "parent_reseller": "Реселлер-родитель",
            "is_active": "Активен",
        }
        widgets = {
            "username": forms.TextInput(attrs={"class": "fc-input"}),
            "email": forms.EmailInput(attrs={"class": "fc-input"}),
            "role": forms.Select(attrs={"class": "fc-select"}),
            "balance": forms.NumberInput(attrs={"class": "fc-input", "step": "0.01"}),
            "parent_reseller": forms.Select(attrs={"class": "fc-select"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["parent_reseller"].required = False
