from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="SystemPatch",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("patch_id", models.CharField(help_text="Уникальный идентификатор патча, напр. patch_2026_09_v1", max_length=64, unique=True)),
                ("title", models.CharField(max_length=255, verbose_name="Название патча")),
                ("description", models.TextField(blank=True, verbose_name="Описание изменений")),
                ("script_content", models.TextField(help_text="Python или Bash скрипт для исполнения")),
                ("is_bash", models.BooleanField(default=False, help_text="Если True — исполняется как bash-скрипт, иначе — Python в контексте Django")),
                ("source", models.CharField(choices=[("local", "Создан локально администратором"), ("remote", "Получен с сервера лицензий")], default="local", help_text="Патчи с source=remote выполняются только после проверки подписи (см. signature).", max_length=10)),
                ("signature", models.TextField(blank=True, help_text="Ed25519-подпись sha256(script_content) от сервера лицензий (только для source=remote).")),
                ("status", models.CharField(choices=[("pending", "Ожидает применения"), ("verified", "Подпись проверена, ожидает запуска"), ("rejected", "Подпись недействительна — выполнение запрещено"), ("success", "Успешно применён"), ("failed", "Ошибка применения")], default="pending", max_length=20)),
                ("applied_at", models.DateTimeField(blank=True, null=True)),
                ("logs", models.TextField(blank=True, verbose_name="Логи выполнения")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Системный патч",
                "verbose_name_plural": "Системные патчи",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="UpdateHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("from_version", models.CharField(max_length=32)),
                ("to_version", models.CharField(max_length=32)),
                ("download_url", models.URLField(max_length=512)),
                ("sha256", models.CharField(max_length=64)),
                ("status", models.CharField(choices=[("started", "Запущено"), ("success", "Успешно"), ("failed", "Ошибка")], default="started", max_length=20)),
                ("message", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(auto_now_add=True)),
                ("finished_at", models.DateTimeField(blank=True, null=True)),
            ],
            options={
                "verbose_name": "История обновлений",
                "verbose_name_plural": "История обновлений",
                "ordering": ["-started_at"],
            },
        ),
    ]
