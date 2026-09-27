"""
CLI-инструмент продавца: публикует новую версию панели (или горячий патч)
в releases.json, который отдаёт GET /v1/updates/check. Запускать на своей
машине/сервере лицензий — приватный ключ никогда никуда не передаётся.

Примеры:
    # Полное обновление панели:
    python publish_release.py release --version 1.2.0 \
        --file fluxcore-1.2.0.tar.gz \
        --download-url https://cdn.example.com/fluxcore-1.2.0.tar.gz

    # Горячий патч:
    python publish_release.py patch --patch-id patch_2026_09_v1 \
        --title "Новый протокол Hysteria2" --script ./patch.sh --bash
"""
import argparse
import hashlib
import json
from pathlib import Path

from crypto import sign_bytes

RELEASES_PATH = Path("releases.json")


def _load() -> dict:
    if not RELEASES_PATH.exists():
        return {"latest_version": "0.0.0", "patches": []}
    return json.loads(RELEASES_PATH.read_text())


def _save(data: dict) -> None:
    RELEASES_PATH.write_text(json.dumps(data, indent=2, ensure_ascii=False))


def cmd_release(args):
    file_bytes = Path(args.file).read_bytes()
    sha256_hex = hashlib.sha256(file_bytes).hexdigest()
    signature = sign_bytes(bytes.fromhex(sha256_hex))

    data = _load()
    data["latest_version"] = args.version
    data["download_url"] = args.download_url
    data["sha256"] = sha256_hex
    data["signature"] = signature
    _save(data)

    print(f"Опубликован релиз {args.version}")
    print(f"  sha256:     {sha256_hex}")
    print(f"  signature:  {signature}")


def cmd_patch(args):
    script_content = Path(args.script).read_text()
    digest = hashlib.sha256(script_content.encode()).digest()
    signature = sign_bytes(digest)

    data = _load()
    patches = [p for p in data.get("patches", []) if p["patch_id"] != args.patch_id]
    patches.append({
        "patch_id": args.patch_id,
        "title": args.title,
        "description": args.description or "",
        "is_bash": args.bash,
        "script_content": script_content,
        "signature": signature,
    })
    data["patches"] = patches
    _save(data)

    print(f"Опубликован патч {args.patch_id}")
    print(f"  signature:  {signature}")


def main():
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="command", required=True)

    p_release = sub.add_parser("release", help="Опубликовать полное обновление панели")
    p_release.add_argument("--version", required=True)
    p_release.add_argument("--file", required=True, help="Путь к tar.gz с новым кодом (для вычисления sha256)")
    p_release.add_argument("--download-url", required=True, help="Публичный URL, откуда панель скачает этот файл")
    p_release.set_defaults(func=cmd_release)

    p_patch = sub.add_parser("patch", help="Опубликовать горячий патч")
    p_patch.add_argument("--patch-id", required=True)
    p_patch.add_argument("--title", required=True)
    p_patch.add_argument("--description", default="")
    p_patch.add_argument("--script", required=True, help="Путь к файлу со скриптом патча")
    p_patch.add_argument("--bash", action="store_true", help="Скрипт — bash (по умолчанию — Python)")
    p_patch.set_defaults(func=cmd_patch)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
