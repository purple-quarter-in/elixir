# Generated by Django 4.2.3 on 2023-08-21 07:44

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("rbac", "0004_accesscategory_content_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="accesscategory",
            name="content_type",
            field=models.JSONField(blank=True, default=list, null=True),
        ),
    ]
