"""
HTTP-демон агента, устанавливаемый на каждую ноду.

Эндпоинты:
- POST /apply-config   — принять и применить конфиги от панели ({"configs": {"xray": {...}, "sing-box": {...}}})
- GET  /health          — статус агента + статус движков (для health-check панели)
- GET  /metrics         — текущие CPU/RAM/диск/трафик/аптайм ноды

Аутентификация — Bearer-токен, сверяется с Node.agent_token, заданным
при установке (см. agent/config.py и install.sh).

Запуск: uvicorn agent.agent:app --host 0.0.0.0 --port 62050
(порт и хост берутся из agent/config.py, но uvicorn CLI параметры их дублируют —
удобнее управлять через systemd unit, см. fluxcore-agent.service).
"""
from typing import Any

from fastapi import Depends, FastAPI, HTTPException, Header
from pydantic import BaseModel

from agent.config import settings
from agent.engines import singbox, xray
from agent.engines.xray import EngineApplyError
from agent.metrics import collect_metrics

app = FastAPI(title="FluxCore Agent")

_ENGINE_MODULES = {
    "xray": xray,
    "sing-box": singbox,
}


def verify_token(authorization: str = Header(default="")) -> None:
    expected = f"Bearer {settings.agent_token}"
    if not settings.agent_token or authorization != expected:
        raise HTTPException(status_code=401, detail="Invalid or missing agent token")


class ApplyConfigRequest(BaseModel):
    configs: dict[str, dict[str, Any]]


@app.post("/apply-config", dependencies=[Depends(verify_token)])
def apply_config(payload: ApplyConfigRequest):
    results = {}
    for engine_name, config in payload.configs.items():
        module = _ENGINE_MODULES.get(engine_name)
        if module is None:
            results[engine_name] = {"ok": False, "error": f"Неизвестный движок: {engine_name}"}
            continue
        try:
            module.apply_config(config)
            results[engine_name] = {"ok": True}
        except EngineApplyError as exc:
            results[engine_name] = {"ok": False, "error": str(exc)}

    all_ok = all(r["ok"] for r in results.values())
    if not all_ok:
        raise HTTPException(status_code=422, detail=results)
    return {"status": "applied", "engines": results}


@app.get("/health", dependencies=[Depends(verify_token)])
def health():
    return {
        "status": "ok",
        "engines": {
            "xray": xray.health_check(),
            "sing-box": singbox.health_check(),
        },
    }


@app.get("/metrics", dependencies=[Depends(verify_token)])
def metrics():
    return collect_metrics()


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.listen_host, port=settings.listen_port)
