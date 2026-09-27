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

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from crypto import sign_token

app = FastAPI(title="FluxCore License Server")

DB_PATH = Path("licenses.json")
RELEASES_PATH = Path("releases.json")
TOKEN_TTL_SECONDS = 24 * 3600  # токен активации живёт 24 часа


def _load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    return json.loads(DB_PATH.read_text())


def _save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2))


def _load_releases() -> dict:
    """
    releases.json пишется ТОЛЬКО через publish_release.py на машине продавца
    (сервер сам ничего сюда не пишет — это read-only витрина).
    Формат: {"latest_version": "1.2.0", "download_url": "...",
    "sha256": "...", "signature": "...", "patches": [...]}
    """
    if not RELEASES_PATH.exists():
        return {}
    return json.loads(RELEASES_PATH.read_text())


class ActivateRequest(BaseModel):
    license_key: str
    hardware_fingerprint: str


class SetTierRequest(BaseModel):
    license_key: str
    tier: str
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
        "tier": record.get("tier") or "lite",
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


@app.post("/v1/set-tier")
def set_tier(payload: SetTierRequest):
    if payload.admin_secret != os.environ.get("ADMIN_SECRET"):
        raise HTTPException(401, "Неверный admin_secret.")
    if payload.tier not in ("lite", "premium", "corporate"):
        raise HTTPException(400, "Недопустимый тариф.")

    db = _load_db()
    if payload.license_key not in db:
        raise HTTPException(404, "Лицензия не найдена.")

    db[payload.license_key]["tier"] = payload.tier
    _save_db(db)
    # Новый тариф попадёт в панель клиента при следующей проверке токена
    # (не позже 12 часов, см. CELERY_BEAT_SCHEDULE в панели).
    return {"status": "ok", "tier": payload.tier}


def _version_tuple(v: str) -> tuple:
    try:
        return tuple(int(p) for p in v.strip().split("."))
    except ValueError:
        return (0,)


@app.get("/v1/updates/check")
def check_updates(current_version: str, x_license_key: str = Header(default="")):
    """
    Панель клиента опрашивает этот эндпоинт (см. apps.updates.services.
    UpdateManager.check_for_updates). Отдаёт данные из releases.json,
    опубликованного продавцом через publish_release.py — сервер сам
    ничего не подписывает "на лету", подпись уже зашита в releases.json.
    Лицензионный ключ передаётся для возможной A/B-выкладки/статистики,
    но отсутствие валидной лицензии не блокирует сам ответ проверки —
    её проверяет отдельно /v1/activate и локальный middleware панели.
    """
    releases = _load_releases()
    if not releases:
        return {"has_update": False, "latest_version": current_version, "patches": []}

    latest_version = releases.get("latest_version", current_version)
    has_update = _version_tuple(latest_version) > _version_tuple(current_version)

    return {
        "has_update": has_update,
        "latest_version": latest_version,
        "download_url": releases.get("download_url") if has_update else None,
        "sha256": releases.get("sha256") if has_update else None,
        "signature": releases.get("signature") if has_update else None,
        "patches": releases.get("patches", []),
    }
