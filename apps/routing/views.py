"""Кастомные CRUD-views для правил маршрутизации — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import RoutingRuleForm
from .models import RoutingRule


@login_required
def routingrule_list_view(request):
    rules = RoutingRule.objects.select_related("node", "target_outbound").order_by("node__name", "priority")
    return render(request, "routing/routingrule_list.html", {"rules": rules})


@login_required
def routingrule_create_view(request):
    if request.method == "POST":
        form = RoutingRuleForm(request.POST)
        if form.is_valid():
            rule = form.save()
            messages.success(request, f"Правило «{rule.name}» создано.")
            return redirect("dashboard:routingrule-list")
    else:
        form = RoutingRuleForm()

    return render(request, "routing/routingrule_form.html", {"form": form, "is_edit": False})


@login_required
def routingrule_edit_view(request, pk):
    rule = get_object_or_404(RoutingRule, pk=pk)

    if request.method == "POST":
        form = RoutingRuleForm(request.POST, instance=rule)
        if form.is_valid():
            form.save()
            messages.success(request, f"Правило «{rule.name}» обновлено.")
            return redirect("dashboard:routingrule-list")
    else:
        form = RoutingRuleForm(instance=rule)

    return render(request, "routing/routingrule_form.html", {"form": form, "is_edit": True, "rule": rule})


@login_required
def routingrule_delete_view(request, pk):
    rule = get_object_or_404(RoutingRule, pk=pk)

    if request.method == "POST":
        name = rule.name
        rule.delete()
        messages.success(request, f"Правило «{name}» удалено.")
        return redirect("dashboard:routingrule-list")

    return render(request, "routing/routingrule_confirm_delete.html", {"rule": rule})
