"""Кастомные CRUD-views для пользователей — в дизайне дашборда, без Django admin."""
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render

from .user_forms import UserCreateForm, UserEditForm

User = get_user_model()


@login_required
def user_list_view(request):
    users = User.objects.select_related("parent_reseller").order_by("-date_joined")
    return render(request, "accounts/user_list.html", {"users": users})


@login_required
def user_create_view(request):
    if request.method == "POST":
        form = UserCreateForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, f"Пользователь «{user.username}» создан.")
            return redirect("dashboard:user-list")
    else:
        form = UserCreateForm()

    return render(request, "accounts/user_form.html", {"form": form, "is_edit": False})


@login_required
def user_edit_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        form = UserEditForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, f"Пользователь «{user.username}» обновлён.")
            return redirect("dashboard:user-list")
    else:
        form = UserEditForm(instance=user)

    return render(request, "accounts/user_form.html", {"form": form, "is_edit": True, "user_obj": user})


@login_required
def user_delete_view(request, pk):
    user = get_object_or_404(User, pk=pk)

    if request.method == "POST":
        username = user.username
        user.delete()
        messages.success(request, f"Пользователь «{username}» удалён.")
        return redirect("dashboard:user-list")

    return render(request, "accounts/user_confirm_delete.html", {"user_obj": user})
