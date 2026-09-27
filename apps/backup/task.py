import os
import subprocess
import tarfile
from datetime import datetime

from celery import shared_task
from django.conf import settings

from .crypto import encrypt_file
from .models import BackupTask

BACKUP_DIR = getattr(settings, "BACKUP_DIR", os.path.join(settings.BASE_DIR, "backups"))

# Что, помимо дампа БД, попадает в архив (ТЗ: "конфигурационных файлов,
# сертификатов и ключей"). Секреты нод (Reality-ключи и т.п.) уже хранятся
# зашифрованными прямо в БД (см. apps.licensing.crypto) — их бэкапит pg_dump.
# .env — конфигурация деплоя; media/ — загруженные файлы (лого/favicon
# White Label и т.п.); certs/, если существует — сертификаты, если админ
# хранит их локально рядом с проектом, а не только у nginx/certbot.
EXTRA_BACKUP_PATHS = ["media", "certs"]


@shared_task(bind=True, soft_time_limit=1800, time_limit=1860)
def create_system_backup(self, backup_id: int, password: str | None = None):
    try:
        backup = BackupTask.objects.get(pk=backup_id)
    except BackupTask.DoesNotExist:
        return

    backup.status = BackupTask.Status.PROCESSING
    backup.save(update_fields=["status"])

    os.makedirs(BACKUP_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    archive_name = f"fluxcore_backup_{timestamp}.tar.gz"
    archive_path = os.path.join(BACKUP_DIR, archive_name)
    dump_sql_path = os.path.join(BACKUP_DIR, f"db_dump_{timestamp}.sql")

    try:
        # 1. Дамп PostgreSQL через pg_dump
        db_conf = settings.DATABASES["default"]
        env = os.environ.copy()
        if db_conf.get("PASSWORD"):
            env["PGPASSWORD"] = db_conf["PASSWORD"]

        dump_cmd = [
            "pg_dump",
            "-h", db_conf.get("HOST", "localhost"),
            "-p", str(db_conf.get("PORT", 5432)),
            "-U", db_conf.get("USER", "fluxcore_user"),
            "-f", dump_sql_path,
            db_conf["NAME"],
        ]
        subprocess.run(dump_cmd, env=env, check=True, capture_output=True, text=True)

        # 2. Упаковка дампа БД + .env + конфигурационных файлов в tar.gz
        with tarfile.open(archive_path, "w:gz") as tar:
            tar.add(dump_sql_path, arcname="database.sql")

            env_file = os.path.join(settings.BASE_DIR, ".env")
            if os.path.exists(env_file):
                tar.add(env_file, arcname=".env")

            for rel_path in EXTRA_BACKUP_PATHS:
                abs_path = os.path.join(settings.BASE_DIR, rel_path)
                if os.path.exists(abs_path):
                    tar.add(abs_path, arcname=rel_path)

        # Удаляем временный sql-файл — он уже внутри архива
        if os.path.exists(dump_sql_path):
            os.remove(dump_sql_path)

        # 3. Шифрование паролем (ТЗ: скачиваемый архив — с шифрованием паролем)
        if password:
            encrypted_path = archive_path + ".enc"
            encrypt_file(archive_path, encrypted_path, password)
            os.remove(archive_path)  # исходный незашифрованный tar.gz не оставляем на диске
            archive_path = encrypted_path
            archive_name = os.path.basename(encrypted_path)

        backup.file_name = archive_name
        backup.file_path = archive_path
        backup.file_size = os.path.getsize(archive_path)
        backup.is_encrypted = bool(password)
        backup.status = BackupTask.Status.COMPLETED
        backup.save()

    except subprocess.CalledProcessError as exc:
        _cleanup_temp(dump_sql_path)
        backup.status = BackupTask.Status.FAILED
        backup.error_message = f"pg_dump завершился с ошибкой: {exc.stderr or exc}"
        backup.save()

    except Exception as exc:
        _cleanup_temp(dump_sql_path)
        backup.status = BackupTask.Status.FAILED
        backup.error_message = str(exc)
        backup.save()


def _cleanup_temp(dump_sql_path: str) -> None:
    if os.path.exists(dump_sql_path):
        os.remove(dump_sql_path)
