# Generated by Django 4.2.11 on 2024-09-12 10:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("order", "0005_remove_line_tax_code_remove_lineprice_tax_code_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="line",
            name="tax_code",
            field=models.CharField(
                blank=True, max_length=64, null=True, verbose_name="Налоговый код"
            ),
        ),
        migrations.AddField(
            model_name="lineprice",
            name="tax_code",
            field=models.CharField(
                blank=True, max_length=64, null=True, verbose_name="Налоговый код"
            ),
        ),
        migrations.AddField(
            model_name="surcharge",
            name="tax_code",
            field=models.CharField(
                blank=True, max_length=64, null=True, verbose_name="Налоговый код"
            ),
        ),
    ]
