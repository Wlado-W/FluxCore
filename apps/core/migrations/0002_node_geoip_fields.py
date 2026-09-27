from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="node",
            name="city",
            field=models.CharField(blank=True, help_text="Определяется автоматически по IP (GeoIP)", max_length=100),
        ),
        migrations.AddField(
            model_name="node",
            name="isp",
            field=models.CharField(blank=True, help_text="Определяется автоматически по IP (GeoIP)", max_length=255, verbose_name="Провайдер (ISP)"),
        ),
        migrations.AddField(
            model_name="node",
            name="geo_resolved_at",
            field=models.DateTimeField(blank=True, help_text="Когда гео-данные последний раз обновлялись", null=True),
        ),
    ]
