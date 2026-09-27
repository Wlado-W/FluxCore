"""Кастомные CRUD-views для промокодов — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PromoCodeForm
from .models import PromoCode


@login_required
def promocode_list_view(request):
    promocodes = PromoCode.objects.order_by("-created_at")
    return render(request, "billing/promocode_list.html", {"promocodes": promocodes})


@login_required
def promocode_create_view(request):
    if request.method == "POST":
        form = PromoCodeForm(request.POST)
        if form.is_valid():
            promo = form.save()
            messages.success(request, f"Промокод «{promo.code}» создан.")
            return redirect("dashboard:promocode-list")
    else:
        form = PromoCodeForm()

    return render(request, "billing/promocode_form.html", {"form": form, "is_edit": False})


@login_required
def promocode_edit_view(request, pk):
    promo = get_object_or_404(PromoCode, pk=pk)

    if request.method == "POST":
        form = PromoCodeForm(request.POST, instance=promo)
        if form.is_valid():
            form.save()
            messages.success(request, f"Промокод «{promo.code}» обновлён.")
            return redirect("dashboard:promocode-list")
    else:
        form = PromoCodeForm(instance=promo)

    return render(request, "billing/promocode_form.html", {"form": form, "is_edit": True, "promocode": promo})


@login_required
def promocode_delete_view(request, pk):
    promo = get_object_or_404(PromoCode, pk=pk)

    if request.method == "POST":
        code = promo.code
        promo.delete()
        messages.success(request, f"Промокод «{code}» удалён.")
        return redirect("dashboard:promocode-list")

    return render(request, "billing/promocode_confirm_delete.html", {"promocode": promo})
