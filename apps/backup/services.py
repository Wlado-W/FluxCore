import os
import subprocess
import tarfile
import tempfile

from celery import shared_task
from django.conf import settings

from .crypto import BackupCryptoError, decrypt_file
from .models import BackupTask


class RestoreService:
    @staticmethod
    def restore_from_backup(archive_path: str, is_encrypted: bool = False, password: str | None = None) -> bool:
        """Расшифровывает (если нужно), распаковывает архив и восстанавливает БД."""
        extract_dir = tempfile.mkdtemp(prefix="fluxcore_restore_")
        plain_archive_path = archive_path
        temp_decrypted_path = None

        try:
            if is_encrypted:
                if not password:
                    raise ValueError("Этот бэкап зашифрован — необходим пароль для восстановления.")
                temp_decrypted_path = archive_path + ".decrypted.tmp"
                try:
                    decrypt_file(archive_path, temp_decrypted_path, password)
                except BackupCryptoError as exc:
                    raise ValueError(str(exc)) from exc
                plain_archive_path = temp_decrypted_path

            with tarfile.open(plain_archive_path, "r:gz") as tar:
                # Защита от path traversal (zip/tar-slip): не позволяем
                # членам архива писать за пределы extract_dir через "../" или abs-пути.
                safe_members = []
                extract_root = os.path.realpath(extract_dir)
                for member in tar.getmembers():
                    member_path = os.path.realpath(os.path.join(extract_dir, member.name))
                    if not (member_path == extract_root or member_path.startswith(extract_root + os.sep)):
                        raise ValueError(f"Небезопасный путь внутри архива бэкапа: {member.name}")
                    if member.issym() or member.islnk():
                        raise ValueError(f"Символические/жёсткие ссылки в архиве бэкапа запрещены: {member.name}")
                    safe_members.append(member)
                try:
                    tar.extractall(path=extract_dir, members=safe_members, filter="data")
                except TypeError:
                    # filter= появился в Python 3.12; на более старых версиях просто пропускаем его
                    tar.extractall(path=extract_dir, members=safe_members)

            dump_file = os.path.join(extract_dir, "database.sql")
            if not os.path.exists(dump_file):
                raise FileNotFoundError("В архиве бэкапа отсутствует database.sql")

            db_conf = settings.DATABASES["default"]
            env = os.environ.copy()
            if db_conf.get("PASSWORD"):
                env["PGPASSWORD"] = db_conf["PASSWORD"]

            # Восстановление базы через psql
            restore_cmd = [
                "psql",
                "-h", db_conf.get("HOST", "localhost"),
                "-p", str(db_conf.get("PORT", 5432)),
                "-U", db_conf.get("USER", "fluxcore_user"),
                "-d", db_conf["NAME"],
                "-f", dump_file,
            ]
            subprocess.run(restore_cmd, env=env, check=True, capture_output=True, text=True)

            # media/, certs/ — восстанавливаем поверх текущих (админ уже
            # подтвердил операцию через UI, зная, что это перезапись)
            for rel_path in ("media", "certs"):
                extracted_path = os.path.join(extract_dir, rel_path)
                if os.path.exists(extracted_path):
                    target_path = os.path.join(str(settings.BASE_DIR), rel_path)
                    subprocess.run(["rsync", "-a", f"{extracted_path}/", f"{target_path}/"], check=True)

            return True

        finally:
            if temp_decrypted_path and os.path.exists(temp_decrypted_path):
                os.remove(temp_decrypted_path)
            if os.path.exists(extract_dir):
                subprocess.run(["rm", "-rf", extract_dir])


@shared_task(bind=True, soft_time_limit=1800, time_limit=1860)
def run_restore_backup_task(self, backup_id: int, password: str | None = None):
    try:
        backup = BackupTask.objects.get(pk=backup_id)
    except BackupTask.DoesNotExist:
        return {"success": False, "error": "Бэкап не найден."}

    backup.status = BackupTask.Status.RESTORING
    backup.save(update_fields=["status"])

    try:
        RestoreService.restore_from_backup(
            backup.file_path, is_encrypted=backup.is_encrypted, password=password
        )
        backup.status = BackupTask.Status.RESTORED
        backup.error_message = ""
        backup.save(update_fields=["status", "error_message"])
        return {"success": True}
    except subprocess.CalledProcessError as exc:
        backup.status = BackupTask.Status.RESTORE_FAILED
        backup.error_message = f"Команда восстановления завершилась с ошибкой: {exc.stderr or exc}"
        backup.save(update_fields=["status", "error_message"])
        return {"success": False, "error": backup.error_message}
    except Exception as exc:
        backup.status = BackupTask.Status.RESTORE_FAILED
        backup.error_message = str(exc)
        backup.save(update_fields=["status", "error_message"])
        return {"success": False, "error": str(exc)}
