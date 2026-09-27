"""Кастомные CRUD-views для исходящих — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import OutboundForm
from .models import Outbound


@login_required
def outbound_list_view(request):
    outbounds = Outbound.objects.select_related("node", "target_node").order_by("node__name", "tag")
    return render(request, "outbounds/outbound_list.html", {"outbounds": outbounds})


@login_required
def outbound_create_view(request):
    if request.method == "POST":
        form = OutboundForm(request.POST)
        if form.is_valid():
            outbound = form.save()
            messages.success(request, f"Outbound «{outbound.tag}» создан.")
            return redirect("dashboard:outbound-list")
    else:
        form = OutboundForm()

    return render(request, "outbounds/outbound_form.html", {"form": form, "is_edit": False})


@login_required
def outbound_edit_view(request, pk):
    outbound = get_object_or_404(Outbound, pk=pk)

    if request.method == "POST":
        form = OutboundForm(request.POST, instance=outbound)
        if form.is_valid():
            form.save()
            messages.success(request, f"Outbound «{outbound.tag}» обновлён.")
            return redirect("dashboard:outbound-list")
    else:
        form = OutboundForm(instance=outbound)

    return render(request, "outbounds/outbound_form.html", {"form": form, "is_edit": True, "outbound": outbound})


@login_required
def outbound_delete_view(request, pk):
    outbound = get_object_or_404(Outbound, pk=pk)

    if request.method == "POST":
        tag = outbound.tag
        outbound.delete()
        messages.success(request, f"Outbound «{tag}» удалён.")
        return redirect("dashboard:outbound-list")

    return render(request, "outbounds/outbound_confirm_delete.html", {"outbound": outbound})
