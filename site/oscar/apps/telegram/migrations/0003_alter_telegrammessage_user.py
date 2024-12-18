# Generated by Django 4.2.11 on 2024-11-26 02:41

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("telegram", "0002_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="telegrammessage",
            name="user",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to=settings.AUTH_USER_MODEL,
                verbose_name="Пользователь cайта",
            ),
        ),
    ]
