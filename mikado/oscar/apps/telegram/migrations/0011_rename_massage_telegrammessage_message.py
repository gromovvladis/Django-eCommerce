# Generated by Django 4.2.11 on 2024-09-24 10:19

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("telegram", "0010_rename_telegrammassage_telegrammessage"),
    ]

    operations = [
        migrations.RenameField(
            model_name="telegrammessage",
            old_name="massage",
            new_name="message",
        ),
    ]
