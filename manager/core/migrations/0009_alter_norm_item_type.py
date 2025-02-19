# Generated by Django 5.1.6 on 2025-02-20 11:21

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0008_alter_issue_item_type"),
    ]

    operations = [
        migrations.AlterField(
            model_name="norm",
            name="item_type",
            field=models.CharField(
                help_text="Тип СИЗ (например, ботинки, перчатки)",
                max_length=255,
                unique=True,
                verbose_name="Тип СИЗ",
            ),
        ),
    ]
