"""Применение конфига Xray-core на ноде: запись config.json + рестарт сервиса."""
import json
import subprocess
from pathlib import Path

from agent.config import settings


class EngineApplyError(Exception):
    """Не удалось применить конфиг (валидация или рестарт сервиса провалились)."""


def _validate_config(config_path: str) -> None:
    """Проверяет конфиг через `xray -test`, не запуская сам процесс."""
    result = subprocess.run(
        [settings.xray_binary, "run", "-test", "-config", config_path],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        raise EngineApplyError(f"Xray config validation failed: {result.stderr.strip()}")


def apply_config(config: dict) -> None:
    """Записывает конфиг на диск, валидирует и перезапускает сервис Xray."""
    config_path = Path(settings.xray_config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = config_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    _validate_config(str(tmp_path))

    tmp_path.replace(config_path)

    result = subprocess.run(
        ["systemctl", "restart", settings.xray_service_name],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        raise EngineApplyError(f"Не удалось перезапустить {settings.xray_service_name}: {result.stderr.strip()}")


def health_check() -> bool:
    """Проверяет, что systemd-юнит Xray активен."""
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", settings.xray_service_name],
        timeout=10,
    )
    return result.returncode == 0
