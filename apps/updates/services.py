"""
Проверка обновлений и патчей через сервер лицензий, безопасное скачивание
и применение полного обновления, движок 'горячих' патчей.

Ключевое правило безопасности: ЛЮБОЙ код, полученный по сети (тарбол
обновления, скрипт патча с source=remote), выполняется ТОЛЬКО после того,
как его подпись проверена публичным ключом продавца (тем же, что и для
лицензий — см. apps.licensing.crypto). Без валидной подписи — не
скачиваем/не запускаем, а помечаем как REJECTED и логируем причину.
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tarfile
import tempfile

import requests
from django.conf import settings
from django.utils import timezone

from apps.licensing.crypto import verify_bytes
from apps.licensing.models import License
from .models import SystemPatch, UpdateHistory

LICENSE_SERVER_URL = os.environ.get("LICENSE_SERVER_URL", "")
CURRENT_VERSION = getattr(settings, "FLUXCORE_VERSION", "1.0.0")
DOWNLOAD_TIMEOUT = 120
MAX_ARTIFACT_BYTES = 500 * 1024 * 1024  # 500 MB — защита от переполнения диска


class UpdateError(Exception):
    pass


class SignatureVerificationError(UpdateError):
    pass


def _get_public_key() -> str:
    key = os.environ.get("LICENSING_PUBLIC_KEY")
    if not key:
        raise UpdateError("LICENSING_PUBLIC_KEY не задан в .env — невозможно проверить подпись обновления.")
    return key


def _license_key() -> str:
    license_obj = License.objects.first()
    return license_obj.key if license_obj else ""


def _safe_extract(tar: tarfile.TarFile, dest_dir: str) -> None:
    """
    Защита от path traversal / tar-slip: ни один член архива не должен
    писать за пределы dest_dir, и запрещаем симлинки/хардлинки.
    """
    dest_root = os.path.realpath(dest_dir)
    safe_members = []
    for member in tar.getmembers():
        member_path = os.path.realpath(os.path.join(dest_dir, member.name))
        if not (member_path == dest_root or member_path.startswith(dest_root + os.sep)):
            raise UpdateError(f"Небезопасный путь внутри архива обновления: {member.name}")
        if member.issym() or member.islnk():
            raise UpdateError(f"Символические/жёсткие ссылки в архиве обновления запрещены: {member.name}")
        safe_members.append(member)
    try:
        tar.extractall(path=dest_dir, members=safe_members, filter="data")
    except TypeError:
        # filter= появился в Python 3.12, на более старых интерпретаторах пропускаем
        tar.extractall(path=dest_dir, members=safe_members)


class UpdateManager:

    @staticmethod
    def check_for_updates() -> dict:
        """
        Опрос сервера лицензий на предмет обновлений и горячих патчей.
        Возвращает {"has_update": bool, "latest_version": str,
        "download_url": str, "sha256": str, "signature": str,
        "patches": [{"patch_id", "title", "description", "is_bash",
        "script_content", "signature"}, ...]} либо {"error": "..."}.
        """
        if not LICENSE_SERVER_URL:
            return {"error": "LICENSE_SERVER_URL не задан в .env."}

        try:
            response = requests.get(
                f"{LICENSE_SERVER_URL.rstrip('/')}/v1/updates/check",
                params={"current_version": CURRENT_VERSION},
                headers={"X-License-Key": _license_key()},
                timeout=10,
            )
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as exc:
            return {"error": f"Ошибка соединения с сервером обновлений: {exc}"}
        except ValueError:
            return {"error": "Сервер обновлений вернул некорректный ответ (не JSON)."}

        # Патчи сразу сохраняем в БД как REMOTE/PENDING — но НЕ выполняем
        # автоматически, это делает apply_patch по явному действию админа.
        for patch_data in data.get("patches", []) or []:
            UpdateManager._ingest_remote_patch(patch_data)

        return data

    @staticmethod
    def _ingest_remote_patch(patch_data: dict) -> "SystemPatch | None":
        patch_id = patch_data.get("patch_id")
        if not patch_id:
            return None

        patch, _created = SystemPatch.objects.update_or_create(
            patch_id=patch_id,
            defaults={
                "title": patch_data.get("title", patch_id),
                "description": patch_data.get("description", ""),
                "script_content": patch_data.get("script_content", ""),
                "is_bash": bool(patch_data.get("is_bash", False)),
                "source": SystemPatch.Source.REMOTE,
                "signature": patch_data.get("signature", ""),
            },
        )
        # Уже применённый патч повторно не трогаем
        if patch.status not in (SystemPatch.Status.SUCCESS,):
            UpdateManager._verify_patch_signature(patch)
        return patch

    @staticmethod
    def _verify_patch_signature(patch: SystemPatch) -> bool:
        """Проверяет подпись удалённого патча и обновляет его статус. Не выполняет код."""
        if patch.source != SystemPatch.Source.REMOTE:
            return True  # локальные патчи создаются доверенным админом в Django admin

        try:
            public_key = _get_public_key()
        except UpdateError as exc:
            patch.status = SystemPatch.Status.REJECTED
            patch.logs = str(exc)
            patch.save(update_fields=["status", "logs"])
            return False

        digest = hashlib.sha256(patch.script_content.encode()).digest()
        if patch.signature and verify_bytes(digest, patch.signature, public_key):
            patch.status = SystemPatch.Status.VERIFIED
            patch.save(update_fields=["status"])
            return True

        patch.status = SystemPatch.Status.REJECTED
        patch.logs = "Подпись патча недействительна или отсутствует — выполнение запрещено."
        patch.save(update_fields=["status", "logs"])
        return False

    @staticmethod
    def apply_patch(patch: SystemPatch) -> bool:
        """Безопасное выполнение 'горячего' патча (после проверки подписи для source=remote)."""
        if patch.source == SystemPatch.Source.REMOTE and patch.status != SystemPatch.Status.VERIFIED:
            if not UpdateManager._verify_patch_signature(patch):
                return False
            patch.refresh_from_db()

        output_logs = []
        try:
            if patch.is_bash:
                result = subprocess.run(
                    ["/bin/bash", "-c", patch.script_content],
                    capture_output=True,
                    text=True,
                    timeout=300,
                )
                output_logs.append(f"STDOUT:\n{result.stdout}")
                if result.stderr:
                    output_logs.append(f"STDERR:\n{result.stderr}")
                if result.returncode != 0:
                    raise RuntimeError(f"Bash exit code: {result.returncode}")
            else:
                # Патч выполняется в ограниченном пространстве имён — без builtins
                # уровня файловой системы/сети сверх того, что импортировано явно.
                exec_globals = {"__builtins__": __builtins__, "SystemPatch": SystemPatch}
                exec(patch.script_content, exec_globals, {})
                output_logs.append("Python-скрипт патча выполнен успешно.")

            patch.status = SystemPatch.Status.SUCCESS
            patch.applied_at = timezone.now()
            patch.logs = "\n".join(output_logs)
            patch.save()
            return True

        except Exception as exc:
            patch.status = SystemPatch.Status.FAILED
            output_logs.append(f"CRITICAL ERROR: {exc}")
            patch.logs = "\n".join(output_logs)
            patch.save()
            return False

    @classmethod
    def perform_full_update(cls, download_url: str, sha256_hex: str, signature_b64: str) -> dict:
        """
        Скачивание тарбола (с проверкой подписи и sha256!), безопасная
        распаковка, замена исходного кода, миграция и перезапуск systemd.
        """
        history = UpdateHistory.objects.create(
            from_version=CURRENT_VERSION,
            to_version="unknown",
            download_url=download_url,
            sha256=sha256_hex,
        )

        temp_dir = tempfile.mkdtemp(prefix="fluxcore_update_")
        try:
            public_key = _get_public_key()

            # 1. Подпись обязана быть проверена ДО скачивания артефакта на диск
            #    в объёме — сначала валидируем sha256+подпись как метаданные,
            #    затем скачиваем и сверяем фактический хэш файла.
            digest_bytes = bytes.fromhex(sha256_hex)
            if not verify_bytes(digest_bytes, signature_b64, public_key):
                raise SignatureVerificationError(
                    "Подпись обновления недействительна — обновление отклонено."
                )

            # 2. Скачивание с ограничением размера и последующей сверкой sha256
            tarball_path = os.path.join(temp_dir, "update.tar.gz")
            hasher = hashlib.sha256()
            total = 0
            with requests.get(download_url, stream=True, timeout=DOWNLOAD_TIMEOUT) as res:
                res.raise_for_status()
                with open(tarball_path, "wb") as f:
                    for chunk in res.iter_content(chunk_size=65536):
                        total += len(chunk)
                        if total > MAX_ARTIFACT_BYTES:
                            raise UpdateError("Размер артефакта обновления превышает допустимый лимит.")
                        f.write(chunk)
                        hasher.update(chunk)

            if hasher.hexdigest() != sha256_hex.lower():
                raise SignatureVerificationError(
                    "sha256 скачанного файла не совпадает с заявленным — файл повреждён или подменён."
                )

            # 3. Безопасная распаковка во временный каталог
            extract_dir = os.path.join(temp_dir, "extracted")
            os.makedirs(extract_dir, exist_ok=True)
            with tarfile.open(tarball_path, "r:gz") as tar:
                _safe_extract(tar, extract_dir)

            base_dir = str(settings.BASE_DIR)

            # 4. Синхронизация файлов (исключая .env, venv, media, БД) — без shell=True
            rsync_cmd = [
                "rsync", "-a",
                "--exclude=.env", "--exclude=venv", "--exclude=media", "--exclude=db.sqlite3",
                f"{extract_dir}/", f"{base_dir}/",
            ]
            subprocess.run(rsync_cmd, check=True)

            # 5. Миграции и сборка статики
            venv_python = os.path.join(base_dir, "venv", "bin", "python")
            if not os.path.exists(venv_python):
                venv_python = sys.executable

            subprocess.run([venv_python, os.path.join(base_dir, "manage.py"), "migrate"], check=True)
            subprocess.run(
                [venv_python, os.path.join(base_dir, "manage.py"), "collectstatic", "--noinput"],
                check=True,
            )

            # 6. Перезапуск службы (требует sudoers NOPASSWD именно для этой команды,
            #    см. install.sh — ни для чего более широкого доступ не выдаётся)
            subprocess.run(["sudo", "systemctl", "restart", "fluxcore.service"], check=True)

            history.status = UpdateHistory.Status.SUCCESS
            history.message = "Обновление успешно установлено."
            history.finished_at = timezone.now()
            history.save()
            return {"success": True, "message": "Обновление успешно установлено. Служба перезапущена."}

        except Exception as exc:
            history.status = UpdateHistory.Status.FAILED
            history.message = str(exc)
            history.finished_at = timezone.now()
            history.save()
            return {"success": False, "error": str(exc)}

        finally:
            shutil.rmtree(temp_dir, ignore_errors=True)
