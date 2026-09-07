"""
Кастомные CRUD-views для управления нодами — в дизайне дашборда, без
использования Django admin. Первая сущность из плана перехода на
полностью кастомный интерфейс (см. апрув пользователя в чате).
"""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from apps.licensing.services import LicenseLimitExceeded, check_node_limit

from .forms import NodeForm
from .models import Node


@login_required
def node_list_view(request):
    nodes = Node.objects.select_related("group").order_by("name")
    return render(request, "core/node_list.html", {"nodes": nodes})


@login_required
def node_create_view(request):
    try:
        check_node_limit(Node.objects.count())
    except LicenseLimitExceeded as exc:
        messages.error(request, str(exc))
        return redirect("dashboard:node-list")

    if request.method == "POST":
        form = NodeForm(request.POST)
        if form.is_valid():
            node = form.save()
            messages.success(request, f"Нода «{node.name}» создана.")
            return redirect("dashboard:node-list")
    else:
        form = NodeForm()

    return render(request, "core/node_form.html", {"form": form, "is_edit": False})


@login_required
def node_edit_view(request, pk):
    node = get_object_or_404(Node, pk=pk)

    if request.method == "POST":
        form = NodeForm(request.POST, instance=node)
        if form.is_valid():
            form.save()
            messages.success(request, f"Нода «{node.name}» обновлена.")
            return redirect("dashboard:node-list")
    else:
        form = NodeForm(instance=node)

    return render(request, "core/node_form.html", {"form": form, "is_edit": True, "node": node})


@login_required
def node_delete_view(request, pk):
    node = get_object_or_404(Node, pk=pk)

    if request.method == "POST":
        name = node.name
        node.delete()
        messages.success(request, f"Нода «{name}» удалена.")
        return redirect("dashboard:node-list")

    return render(request, "core/node_confirm_delete.html", {"node": node})
