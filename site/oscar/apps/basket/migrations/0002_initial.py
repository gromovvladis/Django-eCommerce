# Generated by Django 4.2.11 on 2024-12-18 13:44

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalogue", "0001_initial"),
        ("basket", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="lineattribute",
            name="additional",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="catalogue.additional",
                verbose_name="Дополнительный товар",
            ),
        ),
        migrations.AddField(
            model_name="lineattribute",
            name="line",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="attributes",
                to="basket.line",
                verbose_name="Позиция",
            ),
        ),
        migrations.AddField(
            model_name="lineattribute",
            name="option",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="catalogue.option",
                verbose_name="Опция",
            ),
        ),
        migrations.AddField(
            model_name="line",
            name="basket",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="lines",
                to="basket.basket",
                verbose_name="Корзина",
            ),
        ),
        migrations.AddField(
            model_name="line",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="basket_lines",
                to="catalogue.product",
                verbose_name="Товар",
            ),
        ),
    ]
