"""Кастомные CRUD-views для реселлерских профилей — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ResellerProfileForm
from .models import ResellerProfile


@login_required
def resellerprofile_list_view(request):
    profiles = ResellerProfile.objects.select_related("user").order_by("-created_at")
    return render(request, "resellers/resellerprofile_list.html", {"profiles": profiles})


@login_required
def resellerprofile_create_view(request):
    if request.method == "POST":
        form = ResellerProfileForm(request.POST)
        if form.is_valid():
            profile = form.save()
            messages.success(request, f"Профиль реселлера «{profile.user.username}» создан.")
            return redirect("dashboard:resellerprofile-list")
    else:
        form = ResellerProfileForm()

    return render(request, "resellers/resellerprofile_form.html", {"form": form, "is_edit": False})


@login_required
def resellerprofile_edit_view(request, pk):
    profile = get_object_or_404(ResellerProfile, pk=pk)

    if request.method == "POST":
        form = ResellerProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, f"Профиль реселлера «{profile.user.username}» обновлён.")
            return redirect("dashboard:resellerprofile-list")
    else:
        form = ResellerProfileForm(instance=profile)

    return render(request, "resellers/resellerprofile_form.html", {"form": form, "is_edit": True, "profile": profile})


@login_required
def resellerprofile_delete_view(request, pk):
    profile = get_object_or_404(ResellerProfile, pk=pk)

    if request.method == "POST":
        username = profile.user.username
        profile.delete()
        messages.success(request, f"Профиль реселлера «{username}» удалён.")
        return redirect("dashboard:resellerprofile-list")

    return render(request, "resellers/resellerprofile_confirm_delete.html", {"profile": profile})


@login_required
def resellerprofile_approve_view(request, pk):
    """Быстрое одобрение реселлера прямо из списка."""
    profile = get_object_or_404(ResellerProfile, pk=pk)
    profile.is_approved = True
    profile.save(update_fields=["is_approved"])
    messages.success(request, f"Реселлер «{profile.user.username}» одобрен.")
    return redirect("dashboard:resellerprofile-list")
