"""
CLI-инструмент продавца: выпускает новый лицензионный ключ и заносит его
в базу сервера лицензий (licenses.json). Запускать на своей машине/сервере
лицензий при каждой продаже.

Использование:
    python provision.py --customer "ООО Ромашка" --max-nodes 5
"""
import argparse
import json
import secrets
from pathlib import Path

DB_PATH = Path("licenses.json")


def load_db() -> dict:
    if not DB_PATH.exists():
        return {}
    return json.loads(DB_PATH.read_text())


def save_db(db: dict) -> None:
    DB_PATH.write_text(json.dumps(db, indent=2))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--customer", required=True)
    parser.add_argument("--max-nodes", type=int, default=None)
    args = parser.parse_args()

    license_key = secrets.token_urlsafe(24)

    db = load_db()
    db[license_key] = {
        "customer": args.customer,
        "max_nodes": args.max_nodes,
        "hardware_fingerprint": None,  # привяжется автоматически при первой активации клиентом
        "revoked": False,
    }
    save_db(db)

    print(f"Лицензионный ключ для «{args.customer}»:\n{license_key}")


if __name__ == "__main__":
    main()
