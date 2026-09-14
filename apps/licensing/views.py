"""View для активации лицензии через удалённый сервер лицензий продавца."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils import timezone

from .forms import LicenseActivationForm
from .services import LicenseError, activate_license, get_current_license
from .models import RemoteActivationToken


@login_required
def license_view(request):
    current_license = get_current_license()
    current_token = RemoteActivationToken.objects.order_by("-fetched_at").first()
    token_is_valid = bool(current_token and current_token.expires_at > timezone.now())

    if request.method == "POST":
        form = LicenseActivationForm(request.POST)
        if form.is_valid():
            try:
                activate_license(form.cleaned_data["license_key"].strip())
                messages.success(request, "Лицензия активирована через сервер продавца.")
                return redirect("licensing:status")
            except LicenseError as exc:
                messages.error(request, str(exc))
    else:
        form = LicenseActivationForm()

    return render(request, "licensing/status.html", {
        "license": current_license, "token": current_token,
        "token_is_valid": token_is_valid, "form": form,
    })
