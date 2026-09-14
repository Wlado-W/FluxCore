"""
Сервер лицензий FluxCore — держит ТОЛЬКО продавец, на СВОЁМ отдельном
сервере (не отдаётся клиентам вместе с панелью!).

Ключи выпускаются ЗАРАНЕЕ через provision.py при продаже — сервер НЕ
регистрирует произвольные строки как валидные лицензии, только те,
что явно занесены в базу.

Запуск: uvicorn server:app --host 0.0.0.0 --port 8443
(рекомендуется за nginx с HTTPS)
"""
import json
import os
import time
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from crypto import sign_token

app = FastAPI(title="FluxCore License Server")

DB_PATH = Path("licenses.json")
TOKEN_TTL_SECONDS = 24 * 3600  # токен активации живёт 24 часа


def _load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    return json.loads(DB_PATH.read_text())


def _save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2))


class ActivateRequest(BaseModel):
    license_key: str
    hardware_fingerprint: str


class RevokeRequest(BaseModel):
    license_key: str
    admin_secret: str


@app.post("/v1/activate")
def activate(payload: ActivateRequest):
    db = _load_db()
    record = db.get(payload.license_key)

    if record is None:
        # Ключ не был выпущен через provision.py — значит невалиден.
        # НИКОГДА не регистрируем неизвестные ключи автоматически.
        raise HTTPException(404, "Лицензионный ключ не найден.")

    if record["revoked"]:
        raise HTTPException(403, "Лицензия отозвана.")

    if record["hardware_fingerprint"] is None:
        # Первая активация — привязываем ключ к железу этого сервера
        record["hardware_fingerprint"] = payload.hardware_fingerprint
        db[payload.license_key] = record
        _save_db(db)
    elif record["hardware_fingerprint"] != payload.hardware_fingerprint:
        raise HTTPException(403, "Лицензия уже активирована на другом сервере.")

    token_payload = {
        "license_key": payload.license_key,
        "hardware_fingerprint": payload.hardware_fingerprint,
        "max_nodes": record.get("max_nodes"),
        "issued_at": int(time.time()),
        "expires_at": int(time.time()) + TOKEN_TTL_SECONDS,
    }
    token = sign_token(token_payload)

    return {"token": token, "expires_in": TOKEN_TTL_SECONDS}


@app.post("/v1/revoke")
def revoke(payload: RevokeRequest):
    if payload.admin_secret != os.environ.get("ADMIN_SECRET"):
        raise HTTPException(401, "Неверный admin_secret.")

    db = _load_db()
    if payload.license_key not in db:
        raise HTTPException(404, "Лицензия не найдена.")

    db[payload.license_key]["revoked"] = True
    _save_db(db)
    return {"status": "revoked"}
