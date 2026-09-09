"""
Кастомная view для просмотра аудит-лога — в дизайне дашборда, без Django
admin. Лог полностью read-only (создаётся только автоматически сигналами,
см. apps/audit/signals.py) — здесь нет create/edit/delete.
"""
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import render

from .models import AuditLog


@login_required
def auditlog_list_view(request):
    logs = AuditLog.objects.select_related("actor").order_by("-created_at")

    action_filter = request.GET.get("action")
    if action_filter:
        logs = logs.filter(action=action_filter)

    model_filter = request.GET.get("model")
    if model_filter:
        logs = logs.filter(model_name=model_filter)

    paginator = Paginator(logs, 50)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "audit/auditlog_list.html", {
        "page_obj": page_obj,
        "action_choices": AuditLog.Action.choices,
        "current_action": action_filter or "",
        "current_model": model_filter or "",
        "model_names": AuditLog.objects.values_list("model_name", flat=True).distinct().order_by("model_name"),
    })
