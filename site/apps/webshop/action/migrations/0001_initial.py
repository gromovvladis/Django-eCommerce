# Generated by Django 4.2.11 on 2025-03-19 10:47

import core.models.fields.autoslugfield
import core.models.img.paths
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Action",
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
                    "slug",
                    core.models.fields.autoslugfield.AutoSlugField(
                        allow_unicode=True,
                        blank=True,
                        editable=False,
                        max_length=128,
                        overwrite=True,
                        populate_from="title",
                        unique=True,
                        verbose_name="Ярлык",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        upload_to=core.models.img.paths.get_image_actions_upload_path
                    ),
                ),
                ("title", models.CharField(max_length=128, verbose_name="Заголовок")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("order", models.IntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True)),
                (
                    "date_created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "date_updated",
                    models.DateTimeField(auto_now=True, verbose_name="Дата изменения"),
                ),
                (
                    "meta_title",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Мета заголовок",
                    ),
                ),
                (
                    "meta_description",
                    models.TextField(
                        blank=True, null=True, verbose_name="Мета описание"
                    ),
                ),
            ],
            options={
                "verbose_name": "Акция-баннер",
                "verbose_name_plural": "Акции-баннеры",
                "ordering": ["order", "title"],
            },
        ),
        migrations.CreateModel(
            name="ActionProduct",
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
                ("display_order", models.IntegerField(default=0)),
            ],
        ),
        migrations.CreateModel(
            name="PromoCategory",
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
                    "slug",
                    core.models.fields.autoslugfield.AutoSlugField(
                        allow_unicode=True,
                        blank=True,
                        editable=False,
                        max_length=128,
                        overwrite=True,
                        populate_from="title",
                        unique=True,
                        verbose_name="Ярлык",
                    ),
                ),
                (
                    "image",
                    models.ImageField(
                        blank=True,
                        upload_to=core.models.img.paths.get_image_promocategory_upload_path,
                    ),
                ),
                ("title", models.CharField(max_length=128, verbose_name="Заголовок")),
                ("description", models.TextField(blank=True, verbose_name="Описание")),
                ("order", models.IntegerField(default=0, verbose_name="Порядок")),
                ("is_active", models.BooleanField(default=True)),
                (
                    "date_created",
                    models.DateTimeField(
                        auto_now_add=True, verbose_name="Дата создания"
                    ),
                ),
                (
                    "date_updated",
                    models.DateTimeField(auto_now=True, verbose_name="Дата изменения"),
                ),
                (
                    "meta_title",
                    models.CharField(
                        blank=True,
                        max_length=255,
                        null=True,
                        verbose_name="Мета заголовок",
                    ),
                ),
                (
                    "meta_description",
                    models.TextField(
                        blank=True, null=True, verbose_name="Мета описание"
                    ),
                ),
                (
                    "type",
                    models.CharField(
                        choices=[
                            ("PROMO", "Промо-категория"),
                            ("RECOMEND", "Рекомендованные товары"),
                            ("ACTION", "Акция на товары"),
                        ],
                        default="RECOMEND",
                        max_length=255,
                        verbose_name="Тип категории",
                    ),
                ),
            ],
            options={
                "verbose_name": "Промо-товар",
                "verbose_name_plural": "Промо-товары",
                "ordering": ["order", "title"],
            },
        ),
        migrations.CreateModel(
            name="PromoCategoryProduct",
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
                ("display_order", models.IntegerField(default=0)),
            ],
        ),
    ]
