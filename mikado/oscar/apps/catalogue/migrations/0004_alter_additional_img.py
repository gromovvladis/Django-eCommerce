# Generated by Django 4.2.11 on 2024-07-22 14:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("catalogue", "0003_alter_option_options_alter_option_required_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="additional",
            name="img",
            field=models.ImageField(
                blank=True,
                max_length=255,
                null=True,
                upload_to="additionals",
                verbose_name="Изображение",
            ),
        ),
    ]
