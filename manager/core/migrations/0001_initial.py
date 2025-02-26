# Generated by Django 5.1.6 on 2025-02-26 15:11

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="HeightGroup",
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
                    "level",
                    models.PositiveIntegerField(
                        choices=[(1, "1 группа"), (2, "2 группа"), (3, "3 группа")],
                        unique=True,
                        verbose_name="Уровень",
                    ),
                ),
            ],
            options={
                "verbose_name": "Группа работ на высоте",
                "verbose_name_plural": "Группы работ на высоте",
                "ordering": ["level"],
            },
        ),
        migrations.CreateModel(
            name="Position",
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
                    "position_name",
                    models.CharField(
                        max_length=100, unique=True, verbose_name="Название должности"
                    ),
                ),
            ],
            options={
                "verbose_name": "Должность",
                "verbose_name_plural": "Должности",
            },
        ),
        migrations.CreateModel(
            name="PPEType",
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
                    "name",
                    models.CharField(
                        help_text="Укажите тип средства индивидуальной защиты",
                        max_length=255,
                        unique=True,
                        verbose_name="Тип СИЗ",
                    ),
                ),
                (
                    "default_mu",
                    models.CharField(
                        choices=[
                            ("шт.", "штук"),
                            ("пар.", "пар"),
                            ("компл.", "комплектов"),
                            ("г.", "грамм"),
                            ("мл.", "миллилитров"),
                        ],
                        default="шт.",
                        max_length=10,
                        verbose_name="Единица измерения",
                    ),
                ),
            ],
            options={
                "verbose_name": "Тип СИЗ",
                "verbose_name_plural": "Типы СИЗ",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Employee",
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
                ("first_name", models.CharField(max_length=50, verbose_name="Имя")),
                ("last_name", models.CharField(max_length=50, verbose_name="Фамилия")),
                (
                    "patronymic",
                    models.CharField(max_length=50, verbose_name="Отчество"),
                ),
                (
                    "department",
                    models.CharField(max_length=50, verbose_name="Подразделение"),
                ),
                (
                    "body_size",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("40-42/158-164", "40-42/158-164"),
                            ("44-46/158-164", "44-46/158-164"),
                            ("44-46/170-176", "44-46/170-176"),
                            ("44-46/182-188", "44-46/182-188"),
                            ("44-46/194-200", "44-46/194-200"),
                            ("48-50/158-164", "48-50/158-164"),
                            ("48-50/170-176", "48-50/170-176"),
                            ("48-50/182-188", "48-50/182-188"),
                            ("48-50/194-200", "48-50/194-200"),
                            ("52-54/158-164", "52-54/158-164"),
                            ("52-54/170-176", "52-54/170-176"),
                            ("52-54/182-188", "52-54/182-188"),
                            ("52-54/194-200", "52-54/194-200"),
                            ("56-58/158-164", "56-58/158-164"),
                            ("56-58/170-176", "56-58/170-176"),
                            ("56-58/182-188", "56-58/182-188"),
                            ("56-58/194-200", "56-58/194-200"),
                            ("60-62/158-164", "60-62/158-164"),
                            ("60-62/170-176", "60-62/170-176"),
                            ("60-62/182-188", "60-62/182-188"),
                            ("60-62/194-200", "60-62/194-200"),
                            ("64-66/158-164", "64-66/158-164"),
                            ("64-66/170-176", "64-66/170-176"),
                            ("64-66/182-188", "64-66/182-188"),
                            ("64-66/194-200", "64-66/194-200"),
                            ("68-70/158-164", "68-70/158-164"),
                            ("68-70/170-176", "68-70/170-176"),
                            ("68-70/182-188", "68-70/182-188"),
                            ("68-70/194-200", "68-70/194-200"),
                            ("72-74/194-200", "72-74/194-200"),
                        ],
                        help_text="Пример: 44-46/158-164",
                        max_length=40,
                        null=True,
                        verbose_name="Размер спецодежды (тело)",
                    ),
                ),
                (
                    "head_size",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("51", "51"),
                            ("52", "52"),
                            ("53", "53"),
                            ("54", "54"),
                            ("55", "55"),
                            ("56", "56"),
                            ("57", "57"),
                            ("58", "58"),
                            ("59", "59"),
                            ("60", "60"),
                            ("61", "61"),
                            ("62", "62"),
                            ("63", "63"),
                        ],
                        help_text="Пример: 56, 57, 58",
                        max_length=3,
                        null=True,
                        verbose_name="Размер головного убора",
                    ),
                ),
                (
                    "glove_size",
                    models.FloatField(
                        blank=True,
                        choices=[
                            (6.0, 6.0),
                            (6.5, 6.5),
                            (7.0, 7.0),
                            (7.5, 7.5),
                            (8.0, 8.0),
                            (8.5, 8.5),
                            (9.0, 9.0),
                            (9.5, 9.5),
                            (10.0, 10.0),
                            (10.5, 10.5),
                            (11.0, 11.0),
                            (11.5, 11.5),
                            (12.0, 12.0),
                        ],
                        help_text="Пример: 8.0, 8.5 ... 11.0",
                        null=True,
                        verbose_name="Размер перчаток",
                    ),
                ),
                (
                    "shoe_size",
                    models.IntegerField(
                        blank=True,
                        choices=[
                            (35, "35"),
                            (36, "36"),
                            (37, "37"),
                            (38, "38"),
                            (39, "39"),
                            (40, "40"),
                            (41, "41"),
                            (42, "42"),
                            (43, "43"),
                            (44, "44"),
                            (45, "45"),
                            (46, "46"),
                            (47, "47"),
                            (48, "48"),
                            (49, "49"),
                            (50, "50"),
                            (51, "51"),
                            (52, "52"),
                        ],
                        help_text="Пример: 35, 36 ... 52",
                        null=True,
                        verbose_name="Размер обуви",
                    ),
                ),
                (
                    "height_group",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="core.heightgroup",
                        verbose_name="Группа работ на высоте",
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="employees",
                        to="core.position",
                        verbose_name="Должность",
                    ),
                ),
            ],
            options={
                "verbose_name": "Сотрудник",
                "verbose_name_plural": "Сотрудники",
                "ordering": ["last_name", "first_name", "patronymic"],
            },
        ),
        migrations.CreateModel(
            name="Issue",
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
                    "item_name",
                    models.CharField(
                        help_text="Наименование предмета СИЗ",
                        max_length=255,
                        verbose_name="Наименование предмета",
                    ),
                ),
                ("issue_date", models.DateField(verbose_name="Дата выдачи")),
                (
                    "expiration_date",
                    models.DateField(
                        blank=True, null=True, verbose_name="Срок годности"
                    ),
                ),
                (
                    "is_active",
                    models.BooleanField(default=True, verbose_name="Активно"),
                ),
                (
                    "item_size",
                    models.CharField(
                        blank=True,
                        help_text="Укажите размер если есть (например, 42, L, 10.5)",
                        max_length=100,
                        null=True,
                        verbose_name="Размер",
                    ),
                ),
                (
                    "item_mu",
                    models.CharField(
                        choices=[
                            ("шт.", "штук"),
                            ("пар.", "пар"),
                            ("компл.", "комплектов"),
                            ("г.", "грамм"),
                            ("мл.", "миллилитров"),
                        ],
                        default="шт.",
                        max_length=10,
                        verbose_name="Единица измерения",
                    ),
                ),
                (
                    "employee",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issues",
                        to="core.employee",
                        verbose_name="Сотрудник",
                    ),
                ),
                (
                    "ppe_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="issues",
                        to="core.ppetype",
                        verbose_name="Тип СИЗ",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="NormHeight",
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
                ("quantity", models.PositiveIntegerField(verbose_name="Количество")),
                (
                    "lifespan",
                    models.PositiveIntegerField(
                        default=6, verbose_name="Срок годности (месяцев)"
                    ),
                ),
                (
                    "height_group",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="norms",
                        to="core.heightgroup",
                    ),
                ),
                (
                    "ppe_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="height_norms",
                        to="core.ppetype",
                    ),
                ),
            ],
            options={
                "verbose_name": "Норма для высотных работ",
                "verbose_name_plural": "Нормы для высотных работ",
                "unique_together": {("height_group", "ppe_type")},
            },
        ),
        migrations.CreateModel(
            name="Norm",
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
                    "quantity",
                    models.PositiveIntegerField(
                        help_text="Сколько единиц СИЗ положено для этой должности",
                        verbose_name="Количество",
                    ),
                ),
                (
                    "lifespan",
                    models.PositiveIntegerField(
                        default=12, verbose_name="Срок годности (месяцев)"
                    ),
                ),
                (
                    "position",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="norms",
                        to="core.position",
                    ),
                ),
                (
                    "ppe_type",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="norms",
                        to="core.ppetype",
                    ),
                ),
            ],
            options={
                "verbose_name": "Норма выдачи",
                "verbose_name_plural": "Нормы выдачи",
                "unique_together": {("position", "ppe_type")},
            },
        ),
    ]
