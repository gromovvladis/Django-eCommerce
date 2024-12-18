# Generated by Django 4.2.11 on 2024-12-11 11:36

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0009_additional_stores"),
    ]

    operations = [
        migrations.AddField(
            model_name="additional",
            name="cost_price",
            field=models.DecimalField(
                decimal_places=2,
                default=0,
                help_text="Закупочная цена за ед. доп товара",
                max_digits=12,
                verbose_name="Цена закупки",
            ),
        ),
        migrations.AlterField(
            model_name="additional",
            name="article",
            field=models.CharField(
                blank=True,
                max_length=128,
                null=True,
                unique=True,
                verbose_name="Уникальный артикул",
            ),
        ),
    ]
