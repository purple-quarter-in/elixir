# Generated by Django 4.2.3 on 2023-08-24 05:39

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("user", "0004_remove_user_group_alter_user_profile"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="user",
            name="group",
        ),
    ]
