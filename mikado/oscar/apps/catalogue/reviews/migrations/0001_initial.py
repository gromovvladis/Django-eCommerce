# Generated by Django 4.2.11 on 2024-11-25 08:45

from django.db import migrations, models
import django.db.models.deletion
import oscar.apps.catalogue.reviews.utils


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("catalogue", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="ProductReview",
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
                    "score",
                    models.SmallIntegerField(
                        choices=[(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5)],
                        verbose_name="Оценка",
                    ),
                ),
                ("body", models.TextField(verbose_name="Текст отзыва")),
                (
                    "status",
                    models.SmallIntegerField(
                        choices=[
                            (0, "Не просмотрен"),
                            (1, "Одобренный"),
                            (2, "Отклоненный"),
                        ],
                        default=oscar.apps.catalogue.reviews.utils.get_default_review_status,
                        verbose_name="Статус",
                    ),
                ),
                ("date_created", models.DateTimeField(auto_now_add=True)),
                (
                    "is_open",
                    models.BooleanField(
                        db_index=True, default=False, verbose_name="Отзыв просмотрен"
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="reviews",
                        to="catalogue.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "Отзыв товара",
                "verbose_name_plural": "Отзывы товаров",
            },
        ),
    ]
