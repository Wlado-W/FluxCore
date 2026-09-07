"""Применение конфига sing-box на ноде: запись config.json + рестарт сервиса."""
import json
import subprocess
from pathlib import Path

from agent.config import settings
from agent.engines.xray import EngineApplyError


def _validate_config(config_path: str) -> None:
    """Проверяет конфиг через `sing-box check`."""
    result = subprocess.run(
        [settings.singbox_binary, "check", "-c", config_path],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        raise EngineApplyError(f"sing-box config validation failed: {result.stderr.strip()}")


def apply_config(config: dict) -> None:
    """Записывает конфиг на диск, валидирует и перезапускает сервис sing-box."""
    config_path = Path(settings.singbox_config_path)
    config_path.parent.mkdir(parents=True, exist_ok=True)

    tmp_path = config_path.with_suffix(".tmp")
    tmp_path.write_text(json.dumps(config, indent=2, ensure_ascii=False))

    _validate_config(str(tmp_path))

    tmp_path.replace(config_path)

    result = subprocess.run(
        ["systemctl", "restart", settings.singbox_service_name],
        capture_output=True, text=True, timeout=15,
    )
    if result.returncode != 0:
        raise EngineApplyError(
            f"Не удалось перезапустить {settings.singbox_service_name}: {result.stderr.strip()}"
        )


def health_check() -> bool:
    """Проверяет, что systemd-юнит sing-box активен."""
    result = subprocess.run(
        ["systemctl", "is-active", "--quiet", settings.singbox_service_name],
        timeout=10,
    )
    return result.returncode == 0
