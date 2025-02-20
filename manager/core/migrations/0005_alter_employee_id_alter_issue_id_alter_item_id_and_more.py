# Generated by Django 5.1.6 on 2025-02-20 08:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("core", "0004_auto_20250220_0852"),
    ]

    operations = [
        migrations.AlterField(
            model_name="employee",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="issue",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="item",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="norm",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
        migrations.AlterField(
            model_name="norm",
            name="item_type",
            field=models.CharField(
                default="Ботинки",
                help_text="Тип СИЗ (например, ботинки, перчатки)",
                max_length=255,
                unique=True,
                verbose_name="Тип СИЗ",
            ),
        ),
        migrations.AlterField(
            model_name="position",
            name="id",
            field=models.BigAutoField(
                auto_created=True, primary_key=True, serialize=False, verbose_name="ID"
            ),
        ),
    ]
