"""Кастомные CRUD-views для клиентов — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ClientForm
from .models import Client


@login_required
def client_list_view(request):
    clients = Client.objects.select_related("owner", "group").order_by("-created_at")
    return render(request, "clients/client_list.html", {"clients": clients})


@login_required
def client_create_view(request):
    if request.method == "POST":
        form = ClientForm(request.POST)
        if form.is_valid():
            client = form.save()
            messages.success(request, f"Клиент «{client.name}» создан.")
            return redirect("dashboard:client-list")
    else:
        form = ClientForm()

    return render(request, "clients/client_form.html", {"form": form, "is_edit": False})


@login_required
def client_edit_view(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == "POST":
        form = ClientForm(request.POST, instance=client)
        if form.is_valid():
            form.save()
            messages.success(request, f"Клиент «{client.name}» обновлён.")
            return redirect("dashboard:client-list")
    else:
        form = ClientForm(instance=client)

    return render(request, "clients/client_form.html", {"form": form, "is_edit": True, "client": client})


@login_required
def client_delete_view(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == "POST":
        name = client.name
        client.delete()
        messages.success(request, f"Клиент «{name}» удалён.")
        return redirect("dashboard:client-list")

    return render(request, "clients/client_confirm_delete.html", {"client": client})
