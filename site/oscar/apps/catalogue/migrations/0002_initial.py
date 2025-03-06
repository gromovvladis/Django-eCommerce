# Generated by Django 4.2.11 on 2025-02-28 10:16

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("store", "0001_initial"),
        ("catalogue", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="additional",
            name="stores",
            field=models.ManyToManyField(
                blank=True, to="store.store", verbose_name="Магазины"
            ),
        ),
        migrations.AlterUniqueTogether(
            name="productrecommendation",
            unique_together={("primary", "recommendation")},
        ),
        migrations.AlterUniqueTogether(
            name="productcategory",
            unique_together={("product", "category")},
        ),
        migrations.AlterUniqueTogether(
            name="productattribute",
            unique_together={("attribute", "product")},
        ),
        migrations.AlterUniqueTogether(
            name="productadditional",
            unique_together={("primary_product", "additional_product")},
        ),
        migrations.AlterUniqueTogether(
            name="attributeoption",
            unique_together={("group", "option")},
        ),
    ]
