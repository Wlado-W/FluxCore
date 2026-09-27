import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="BackupTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("file_name", models.CharField(blank=True, max_length=255, verbose_name="Имя файла")),
                ("file_path", models.CharField(blank=True, max_length=512, verbose_name="Путь к файлу")),
                ("file_size", models.BigIntegerField(default=0, verbose_name="Размер (байты)")),
                ("is_encrypted", models.BooleanField(default=False, verbose_name="Зашифрован паролем")),
                ("status", models.CharField(choices=[("pending", "В очереди"), ("processing", "Создаётся"), ("completed", "Завершено"), ("failed", "Ошибка"), ("restoring", "Восстанавливается"), ("restored", "Восстановлено"), ("restore_failed", "Ошибка восстановления")], default="pending", max_length=20)),
                ("error_message", models.TextField(blank=True, verbose_name="Текст ошибки")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("created_by", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="backup_tasks", to=settings.AUTH_USER_MODEL, verbose_name="Создал")),
            ],
            options={
                "verbose_name": "Резервная копия",
                "verbose_name_plural": "Резервные копии",
                "ordering": ["-created_at"],
            },
        ),
    ]
