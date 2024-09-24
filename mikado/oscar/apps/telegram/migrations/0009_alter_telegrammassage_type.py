# Generated by Django 4.2.11 on 2024-09-24 04:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        (
            "telegram",
            "0008_remove_telegrammassage_tg_user_telegrammassage_user_and_more",
        ),
    ]

    operations = [
        migrations.AlterField(
            model_name="telegrammassage",
            name="type",
            field=models.CharField(
                choices=[
                    ("new-order", "Уведомление о новом заказе"),
                    ("status-order", "Уведомление об изменении статуса заказа"),
                    ("technical", "Техническое уведомление"),
                    ("offer", "Уведомление о персональном предложении"),
                    ("misc", "Без типа"),
                ],
                default="misc",
                max_length=128,
                verbose_name="Тип сообщения",
            ),
        ),
    ]
