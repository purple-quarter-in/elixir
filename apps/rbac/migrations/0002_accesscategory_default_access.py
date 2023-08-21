# Generated by Django 4.2.3 on 2023-08-18 17:31

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rbac", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="accesscategory",
            name="default_access",
            field=models.JSONField(
                default={"access": False, "add": False, "change": True, "view": False}
            ),
        ),
    ]
