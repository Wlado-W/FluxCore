"""
Contextvar для передачи текущего request.user и IP из middleware в сигналы
моделей — сигналы (post_save/post_delete) не имеют доступа к request,
поэтому middleware кладёт эти данные сюда перед обработкой view.
"""
from contextvars import ContextVar

_current_actor: ContextVar = ContextVar("audit_current_actor", default=None)
_current_ip: ContextVar = ContextVar("audit_current_ip", default=None)


def set_current_request_context(user, ip_address: str | None) -> None:
    _current_actor.set(user if (user and user.is_authenticated) else None)
    _current_ip.set(ip_address)


def get_current_actor():
    return _current_actor.get()


def get_current_ip():
    return _current_ip.get()


def clear_current_request_context() -> None:
    _current_actor.set(None)
    _current_ip.set(None)
