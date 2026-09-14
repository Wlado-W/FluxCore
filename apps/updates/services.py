import os
import sys
import subprocess
import tarfile
import tempfile
import requests
from django.conf import settings
from django.utils import timezone
from apps.licensing.models import License
from .models import SystemPatch

LICENSE_SERVER_URL = getattr(settings, "LICENSE_SERVER_URL", "https://license.fluxcore.internal")
CURRENT_VERSION = getattr(settings, "FLUXCORE_VERSION", "1.0.0")

class UpdateManager:

    @staticmethod
    def check_for_updates():
        """Опрос сервера лицензий на предмет обновлений и горячих патчей."""
        license_obj = License.objects.first()
        license_key = license_obj.key if license_obj else ""

        try:
            response = requests.get(
                f"{LICENSE_SERVER_URL}/api/v1/updates/check/",
                params={"current_version": CURRENT_VERSION},
                headers={"X-License-Key": license_key},
                timeout=10
            )
            response.raise_for_status()
            return response.json()  # Возвращает: {"has_update": bool, "latest_version": "...", "download_url": "...", "patches": [...]}
        except requests.RequestException as e:
            return {"error": f"Ошибка соединения с сервером обновлений: {str(e)}"}

    @staticmethod
    def apply_patch(patch: SystemPatch) -> bool:
        """Безопасное выполнение 'горячего' патча в изоляции/контексте."""
        patch.status = SystemPatch.Status.PENDING
        patch.save()
        output_logs = []

        try:
            if patch.is_bash:
                # Исполнение Bash-скрипта
                result = subprocess.run(
                    patch.script_content,
                    shell=True,
                    capture_output=True,
                    text=True,
                    executable="/bin/bash",
                    timeout=300
                )
                output_logs.append(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    output_logs.append(f"STDERR:\n{result.stderr}")
                
                if result.returncode != 0:
                    raise RuntimeError(f"Bash exit code: {result.returncode}")
            else:
                # Исполнение Python-кода динамически
                local_scope = {"SystemPatch": SystemPatch}
                exec(patch.script_content, globals(), local_scope)
                output_logs.append("Python script executed successfully.")

            patch.status = SystemPatch.Status.SUCCESS
            patch.applied_at = timezone.now()
            patch.logs = "\n".join(output_logs)
            patch.save()
            return True

        except Exception as e:
            patch.status = SystemPatch.Status.FAILED
            output_logs.append(f"CRITICAL ERROR: {str(e)}")
            patch.logs = "\n".join(output_logs)
            patch.save()
            return False

    @classmethod
    def perform_full_update(cls, download_url: str) -> dict:
        """Скачивание тарбола, замена исходного кода, миграция и перезапуск systemd."""
        temp_dir = tempfile.mkdtemp()
        tarball_path = os.path.join(temp_dir, "update.tar.gz")

        try:
            # 1. Скачивание пакета
            res = requests.get(download_url, stream=True, timeout=60)
            res.raise_for_status()
            with open(tarball_path, "wb") as f:
                for chunk in res.iter_content(chunk_size=8192):
                    f.write(chunk)

            # 2. Распаковка во временный каталог
            extract_dir = os.path.join(temp_dir, "extracted")
            with tarfile.open(tarball_path, "r:gz") as tar:
                tar.extractall(path=extract_dir)

            base_dir = settings.BASE_DIR

            # 3. Синхронизация файлов (исключая .env, venv и media)
            rsync_cmd = (
                f"rsync -av --exclude='.env' --exclude='venv' --exclude='media' "
                f"--exclude='db.sqlite3' {extract_dir}/ {base_dir}/"
            )
            subprocess.run(rsync_cmd, shell=True, check=True)

            # 4. Выполнение миграций и сборка статики
            venv_python = os.path.join(base_dir, "venv", "bin", "python")
            if not os.path.exists(venv_python):
                venv_python = sys.executable

            subprocess.run([venv_python, f"{base_dir}/manage.py", "migrate"], check=True)
            subprocess.run([venv_python, f"{base_dir}/manage.py", "collectstatic", "--noinput"], check=True)

            # 5. Перезапуск службы
            subprocess.Popen(["sudo", "systemctl", "restart", "fluxcore.service"])

            return {"success": True, "message": "Обновление успешно установлено. Перезапуск службы..."}

        except Exception as e:
            return {"success": False, "error": str(e)}
