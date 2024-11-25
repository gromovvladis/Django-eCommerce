# Generated by Django 4.2.11 on 2024-11-25 08:45

import apps.sms_auth.utils
from django.db import migrations, models
import phonenumber_field.modelfields


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="PhoneCode",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "phone_number",
                    phonenumber_field.modelfields.PhoneNumberField(
                        max_length=128, region=None, unique=True
                    ),
                ),
                (
                    "code",
                    models.PositiveIntegerField(
                        default=apps.sms_auth.utils.random_code
                    ),
                ),
                (
                    "valid_to",
                    models.DateTimeField(default=apps.sms_auth.utils.valid_to),
                ),
                (
                    "resend_at",
                    models.DateTimeField(default=apps.sms_auth.utils.resend_at),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "Phone code",
                "verbose_name_plural": "Phone codes",
                "ordering": ("created_at",),
            },
        ),
        migrations.CreateModel(
            name="SMSMessage",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created", models.DateTimeField(auto_now_add=True)),
                (
                    "phone_number",
                    models.CharField(max_length=20, verbose_name="Phone number"),
                ),
                (
                    "cost",
                    models.DecimalField(
                        decimal_places=2, max_digits=12, null=True, verbose_name="Cost"
                    ),
                ),
            ],
            options={
                "verbose_name": "Sms log",
                "verbose_name_plural": "Sms log",
            },
        ),
    ]
