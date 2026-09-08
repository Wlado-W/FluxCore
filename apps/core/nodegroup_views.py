"""Кастомные CRUD-views для групп нод (каскадов) — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import NodeGroupForm
from .models import NodeGroup


@login_required
def nodegroup_list_view(request):
    groups = NodeGroup.objects.prefetch_related("nodes").order_by("name")
    return render(request, "core/nodegroup_list.html", {"groups": groups})


@login_required
def nodegroup_create_view(request):
    if request.method == "POST":
        form = NodeGroupForm(request.POST)
        if form.is_valid():
            group = form.save()
            messages.success(request, f"Группа «{group.name}» создана.")
            return redirect("dashboard:nodegroup-list")
    else:
        form = NodeGroupForm()

    return render(request, "core/nodegroup_form.html", {"form": form, "is_edit": False})


@login_required
def nodegroup_edit_view(request, pk):
    group = get_object_or_404(NodeGroup, pk=pk)

    if request.method == "POST":
        form = NodeGroupForm(request.POST, instance=group)
        if form.is_valid():
            form.save()
            messages.success(request, f"Группа «{group.name}» обновлена.")
            return redirect("dashboard:nodegroup-list")
    else:
        form = NodeGroupForm(instance=group)

    return render(request, "core/nodegroup_form.html", {"form": form, "is_edit": True, "group": group})


@login_required
def nodegroup_delete_view(request, pk):
    group = get_object_or_404(NodeGroup, pk=pk)

    if request.method == "POST":
        name = group.name
        group.delete()
        messages.success(request, f"Группа «{name}» удалена.")
        return redirect("dashboard:nodegroup-list")

    return render(request, "core/nodegroup_confirm_delete.html", {"group": group})
