"""
Отпечаток железа сервера — привязывает лицензию к конкретной машине,
чтобы нельзя было просто скопировать рабочую лицензию на второй сервер.
"""
import hashlib
import uuid
from pathlib import Path

_FALLBACK_ID_PATH = Path("/etc/fluxcore-agent/machine-fallback-id")


def get_hardware_fingerprint() -> str:
    """
    На Linux использует /etc/machine-id (стабильный, генерируется ОС при
    установке). Если недоступен (напр. другая ОС или контейнер без него) —
    создаёт и сохраняет свой fallback-идентификатор один раз.
    """
    machine_id_path = Path("/etc/machine-id")
    if machine_id_path.exists():
        raw = machine_id_path.read_text().strip()
    else:
        if _FALLBACK_ID_PATH.exists():
            raw = _FALLBACK_ID_PATH.read_text().strip()
        else:
            raw = str(uuid.uuid4())
            _FALLBACK_ID_PATH.parent.mkdir(parents=True, exist_ok=True)
            _FALLBACK_ID_PATH.write_text(raw)

    return hashlib.sha256(raw.encode()).hexdigest()
