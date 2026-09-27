"""
Конфигурация агента — читается из переменных окружения или из
/etc/fluxcore-agent/agent.env (создаётся install.sh при установке).
"""
import os
from dataclasses import dataclass
from pathlib import Path


def _load_env_file(path: Path) -> None:
    if not path.exists():
        return
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        os.environ.setdefault(key.strip(), value.strip())


_load_env_file(Path("/etc/fluxcore-agent/agent.env"))


@dataclass(frozen=True)
class AgentSettings:
    listen_host: str = os.environ.get("AGENT_LISTEN_HOST", "0.0.0.0")
    listen_port: int = int(os.environ.get("AGENT_LISTEN_PORT", "62050"))
    agent_token: str = os.environ.get("AGENT_TOKEN", "")

    xray_binary: str = os.environ.get("XRAY_BINARY", "/usr/local/bin/xray")
    xray_config_path: str = os.environ.get("XRAY_CONFIG_PATH", "/etc/xray/config.json")
    xray_service_name: str = os.environ.get("XRAY_SERVICE_NAME", "xray")

    singbox_binary: str = os.environ.get("SINGBOX_BINARY", "/usr/local/bin/sing-box")
    singbox_config_path: str = os.environ.get("SINGBOX_CONFIG_PATH", "/etc/sing-box/config.json")
    singbox_service_name: str = os.environ.get("SINGBOX_SERVICE_NAME", "sing-box")


settings = AgentSettings()
