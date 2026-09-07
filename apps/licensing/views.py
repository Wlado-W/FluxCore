"""View для активации лицензии прямо из интерфейса панели (не только через management-команду)."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from .forms import LicenseActivationForm
from .services import LicenseError, activate_license, get_active_license


@login_required
def license_view(request):
    active_license = get_active_license()

    if request.method == "POST":
        form = LicenseActivationForm(request.POST)
        if form.is_valid():
            try:
                activate_license(form.cleaned_data["license_key"].strip())
                messages.success(request, "Лицензия успешно активирована.")
                return redirect("licensing:status")
            except LicenseError as exc:
                messages.error(request, str(exc))
    else:
        form = LicenseActivationForm()

    return render(request, "licensing/status.html", {"license": active_license, "form": form})
