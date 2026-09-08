"""Кастомные CRUD-views для инбаундов — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import InboundForm
from .models import Inbound
from .services.connectivity import test_inbound_connection


@login_required
def inbound_list_view(request):
    inbounds = Inbound.objects.select_related("node").order_by("node__name", "port")
    return render(request, "inbounds/inbound_list.html", {"inbounds": inbounds})


@login_required
def inbound_create_view(request):
    if request.method == "POST":
        form = InboundForm(request.POST)
        if form.is_valid():
            inbound = form.save()
            messages.success(request, f"Inbound «{inbound.tag}» создан.")
            return redirect("dashboard:inbound-list")
    else:
        form = InboundForm()

    return render(request, "inbounds/inbound_form.html", {"form": form, "is_edit": False})


@login_required
def inbound_edit_view(request, pk):
    inbound = get_object_or_404(Inbound, pk=pk)

    if request.method == "POST":
        form = InboundForm(request.POST, instance=inbound)
        if form.is_valid():
            form.save()
            messages.success(request, f"Inbound «{inbound.tag}» обновлён.")
            return redirect("dashboard:inbound-list")
    else:
        form = InboundForm(instance=inbound)

    return render(request, "inbounds/inbound_form.html", {"form": form, "is_edit": True, "inbound": inbound})


@login_required
def inbound_delete_view(request, pk):
    inbound = get_object_or_404(Inbound, pk=pk)

    if request.method == "POST":
        tag = inbound.tag
        inbound.delete()
        messages.success(request, f"Inbound «{tag}» удалён.")
        return redirect("dashboard:inbound-list")

    return render(request, "inbounds/inbound_confirm_delete.html", {"inbound": inbound})


@login_required
def inbound_test_view(request, pk):
    """One-click тест соединения (AJAX, вызывается кнопкой из списка)."""
    inbound = get_object_or_404(Inbound, pk=pk)
    result = test_inbound_connection(inbound)
    return JsonResponse(result)
