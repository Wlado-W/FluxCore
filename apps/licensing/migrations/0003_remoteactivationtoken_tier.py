from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('licensing', '0002_remoteactivationtoken_remove_license_is_valid_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='remoteactivationtoken',
            name='tier',
            field=models.CharField(
                choices=[('lite', 'Lite'), ('premium', 'Premium'), ('corporate', 'Corporate')],
                default='lite',
                max_length=20,
            ),
        ),
    ]
