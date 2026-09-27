"""Кастомные CRUD-views для тарифов — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import TariffForm
from .models import Tariff


@login_required
def tariff_list_view(request):
    tariffs = Tariff.objects.order_by("price")
    return render(request, "billing/tariff_list.html", {"tariffs": tariffs})


@login_required
def tariff_create_view(request):
    if request.method == "POST":
        form = TariffForm(request.POST)
        if form.is_valid():
            tariff = form.save()
            messages.success(request, f"Тариф «{tariff.name}» создан.")
            return redirect("dashboard:tariff-list")
    else:
        form = TariffForm()

    return render(request, "billing/tariff_form.html", {"form": form, "is_edit": False})


@login_required
def tariff_edit_view(request, pk):
    tariff = get_object_or_404(Tariff, pk=pk)

    if request.method == "POST":
        form = TariffForm(request.POST, instance=tariff)
        if form.is_valid():
            form.save()
            messages.success(request, f"Тариф «{tariff.name}» обновлён.")
            return redirect("dashboard:tariff-list")
    else:
        form = TariffForm(instance=tariff)

    return render(request, "billing/tariff_form.html", {"form": form, "is_edit": True, "tariff": tariff})


@login_required
def tariff_delete_view(request, pk):
    tariff = get_object_or_404(Tariff, pk=pk)

    if request.method == "POST":
        name = tariff.name
        try:
            tariff.delete()
        except ProtectedError:
            messages.error(request, f"Нельзя удалить тариф «{name}» — по нему уже есть платежи. Деактивируй его вместо удаления.")
            return redirect("dashboard:tariff-list")
        messages.success(request, f"Тариф «{name}» удалён.")
        return redirect("dashboard:tariff-list")

    return render(request, "billing/tariff_confirm_delete.html", {"tariff": tariff})
