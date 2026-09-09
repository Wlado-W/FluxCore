"""Кастомные CRUD-views для групп клиентов — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import ProtectedError
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientGroupForm
from .models import ClientGroup


@login_required
def clientgroup_list_view(request):
    groups = ClientGroup.objects.prefetch_related("inbounds", "clients").order_by("name")
    return render(request, "clients/clientgroup_list.html", {"groups": groups})


@login_required
def clientgroup_create_view(request):
    if request.method == "POST":
        form = ClientGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f"Группа «{group.name}» создана.")
            return redirect("dashboard:clientgroup-list")
    else:
        form = ClientGroupForm()

    return render(request, "clients/clientgroup_form.html", {"form": form, "is_edit": False})


@login_required
def clientgroup_edit_view(request, pk):
    group = get_object_or_404(ClientGroup, pk=pk)

    if request.method == "POST":
        form = ClientGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Группа «{group.name}» обновлена.")
            return redirect("dashboard:clientgroup-list")
    else:
        form = ClientGroupForm(instance=group)

    return render(request, "clients/clientgroup_form.html", {"form": form, "is_edit": True, "group": group})


@login_required
def clientgroup_delete_view(request, pk):
    group = get_object_or_404(ClientGroup, pk=pk)

    if request.method == "POST":
        name = group.name
        try:
            group.delete()
        except ProtectedError:
            messages.error(request, f"Нельзя удалить группу «{name}» — в ней есть клиенты. Сначала перенеси их в другую группу.")
            return redirect("dashboard:clientgroup-list")
        messages.success(request, f"Группа «{name}» удалена.")
        return redirect("dashboard:clientgroup-list")

    return render(request, "clients/clientgroup_confirm_delete.html", {"group": group})
