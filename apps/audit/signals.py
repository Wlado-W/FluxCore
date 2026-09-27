"""
Сигналы, которые автоматически создают записи AuditLog при создании/
изменении/удалении ключевых моделей, а также при входе/выходе/неудачных
попытках входа пользователей.

Подключается в apps/audit/apps.py::AuditConfig.ready().
"""
from django.contrib.auth.signals import user_logged_in, user_logged_out, user_login_failed
from django.db.models.signals import post_delete, post_save, pre_save

from .context import get_current_actor, get_current_ip
from .models import AuditLog

# Поля, которые исключаем из diff'а — служебные/неинформативные для лога
_EXCLUDED_FIELDS = {"created_at", "updated_at", "password", "totp_secret", "agent_token"}


def _serialize_value(value):
    """Приводит значение поля к JSON-совместимому виду для хранения в changes."""
    if hasattr(value, "pk"):
        return str(value)
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _get_trackable_fields(instance):
    return [
        f for f in instance._meta.concrete_fields
        if f.name not in _EXCLUDED_FIELDS
    ]


def _capture_old_values(sender, instance, **kwargs):
    """pre_save: запоминаем старые значения полей для последующего diff'а."""
    if not instance.pk:
        instance._audit_old_values = {}
        return
    try:
        old_instance = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        instance._audit_old_values = {}
        return
    instance._audit_old_values = {
        f.name: _serialize_value(getattr(old_instance, f.name))
        for f in _get_trackable_fields(instance)
    }


def _log_save(sender, instance, created, **kwargs):
    old_values = getattr(instance, "_audit_old_values", {})
    new_values = {
        f.name: _serialize_value(getattr(instance, f.name))
        for f in _get_trackable_fields(instance)
    }

    if created:
        changes = {}
        action = AuditLog.Action.CREATED
    else:
        changes = {
            field: [old_values.get(field), new_val]
            for field, new_val in new_values.items()
            if old_values.get(field) != new_val
        }
        if not changes:
            return  # save() без реальных изменений полей — не логируем
        action = AuditLog.Action.UPDATED

    AuditLog.objects.create(
        actor=get_current_actor(),
        action=action,
        model_name=f"{sender._meta.app_label}.{sender.__name__}",
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        changes=changes,
        ip_address=get_current_ip(),
    )


def _log_delete(sender, instance, **kwargs):
    AuditLog.objects.create(
        actor=get_current_actor(),
        action=AuditLog.Action.DELETED,
        model_name=f"{sender._meta.app_label}.{sender.__name__}",
        object_id=str(instance.pk),
        object_repr=str(instance)[:255],
        ip_address=get_current_ip(),
    )


def _log_login(sender, request, user, **kwargs):
    AuditLog.objects.create(
        actor=user, action=AuditLog.Action.LOGIN,
        ip_address=get_current_ip(),
    )


def _log_logout(sender, request, user, **kwargs):
    AuditLog.objects.create(
        actor=user, action=AuditLog.Action.LOGOUT,
        ip_address=get_current_ip(),
    )


def _log_login_failed(sender, credentials, **kwargs):
    AuditLog.objects.create(
        actor=None, action=AuditLog.Action.LOGIN_FAILED,
        object_repr=credentials.get("username", "")[:255],
        ip_address=get_current_ip(),
    )


def connect_audit_signals_for(model):
    """Подключает pre_save/post_save/post_delete для указанной модели."""
    pre_save.connect(_capture_old_values, sender=model, weak=False)
    post_save.connect(_log_save, sender=model, weak=False)
    post_delete.connect(_log_delete, sender=model, weak=False)


def connect_all_signals():
    """Вызывается из AuditConfig.ready() — подключает все отслеживаемые модели."""
    from apps.clients.models import Client, ClientGroup
    from apps.core.models import Node, NodeGroup
    from apps.inbounds.models import Inbound
    from apps.outbounds.models import Outbound
    from apps.routing.models import RoutingRule

    for model in (Node, NodeGroup, Inbound, Outbound, RoutingRule, Client, ClientGroup):
        connect_audit_signals_for(model)

    user_logged_in.connect(_log_login, weak=False)
    user_logged_out.connect(_log_logout, weak=False)
    user_login_failed.connect(_log_login_failed, weak=False)
