# Generated by Django 4.2.11 on 2024-09-12 04:16

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0003_order_partner"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="order",
            name="partner",
        ),
    ]
