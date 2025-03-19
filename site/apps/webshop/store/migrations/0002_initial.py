# Generated by Django 4.2.11 on 2025-03-19 10:47

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("store", "0001_initial"),
        ("catalogue", "0002_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="storecashtransaction",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="cash_transactions",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Сотрудник",
            ),
        ),
        migrations.AddField(
            model_name="storecash",
            name="store",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="cash",
                to="store.store",
                verbose_name="Магазин",
            ),
        ),
        migrations.AddField(
            model_name="storeaddress",
            name="store",
            field=models.OneToOneField(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="address",
                to="store.store",
                verbose_name="Магазин",
            ),
        ),
        migrations.AddField(
            model_name="store",
            name="terminals",
            field=models.ManyToManyField(
                blank=True,
                related_name="stores",
                to="store.terminal",
                verbose_name="Терминал",
            ),
        ),
        migrations.AddField(
            model_name="store",
            name="users",
            field=models.ManyToManyField(
                blank=True,
                db_index=True,
                related_name="stores",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Персонал",
            ),
        ),
        migrations.AddField(
            model_name="stockrecordoperation",
            name="stockrecord",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="operations",
                to="store.stockrecord",
                verbose_name="Товарная запись",
            ),
        ),
        migrations.AddField(
            model_name="stockrecordoperation",
            name="user",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="stockrecord_operations",
                to=settings.AUTH_USER_MODEL,
                verbose_name="Сотрудник",
            ),
        ),
        migrations.AddField(
            model_name="stockrecord",
            name="product",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stockrecords",
                to="catalogue.product",
                verbose_name="Товар",
            ),
        ),
        migrations.AddField(
            model_name="stockrecord",
            name="store",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="stockrecords",
                to="store.store",
                verbose_name="Магазин",
            ),
        ),
        migrations.AddField(
            model_name="stockalert",
            name="stockrecord",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="alerts",
                to="store.stockrecord",
                verbose_name="Товарная запись",
            ),
        ),
        migrations.AlterUniqueTogether(
            name="stockrecord",
            unique_together={("store", "product")},
        ),
    ]
