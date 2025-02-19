# Generated by Django 2.2.16 on 2025-02-19 18:19

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=50, verbose_name='Фамилия')),
                ('patronymic', models.CharField(max_length=50, verbose_name='Отчество')),
                ('department', models.CharField(max_length=50, verbose_name='Подразделение')),
                ('body_size', models.CharField(blank=True, choices=[('40-42/158-164', '40-42/158-164'), ('44-46/158-164', '44-46/158-164'), ('44-46/170-176', '44-46/170-176'), ('44-46/182-188', '44-46/182-188'), ('44-46/194-200', '44-46/194-200'), ('48-50/158-164', '48-50/158-164'), ('48-50/170-176', '48-50/170-176'), ('48-50/182-188', '48-50/182-188'), ('48-50/194-200', '48-50/194-200'), ('52-54/158-164', '52-54/158-164'), ('52-54/170-176', '52-54/170-176'), ('52-54/182-188', '52-54/182-188'), ('52-54/194-200', '52-54/194-200'), ('56-58/158-164', '56-58/158-164'), ('56-58/170-176', '56-58/170-176'), ('56-58/182-188', '56-58/182-188'), ('56-58/194-200', '56-58/194-200'), ('60-62/158-164', '60-62/158-164'), ('60-62/170-176', '60-62/170-176'), ('60-62/182-188', '60-62/182-188'), ('60-62/194-200', '60-62/194-200'), ('64-66/158-164', '64-66/158-164'), ('64-66/170-176', '64-66/170-176'), ('64-66/182-188', '64-66/182-188'), ('64-66/194-200', '64-66/194-200'), ('68-70/158-164', '68-70/158-164'), ('68-70/170-176', '68-70/170-176'), ('68-70/182-188', '68-70/182-188'), ('68-70/194-200', '68-70/194-200'), ('72-74/194-200', '72-74/194-200')], help_text='Пример: 44-46/158-164', max_length=40, null=True, verbose_name='Размер спецодежды (тело)')),
                ('head_size', models.CharField(blank=True, choices=[('51', '51'), ('52', '52'), ('53', '53'), ('54', '54'), ('55', '55'), ('56', '56'), ('57', '57'), ('58', '58'), ('59', '59'), ('60', '60'), ('61', '61'), ('62', '62'), ('63', '63')], help_text='Пример: 56, 57, 58', max_length=3, null=True, verbose_name='Размер головного убора')),
                ('glove_size', models.CharField(blank=True, choices=[(6.0, 6.0), (6.5, 6.5), (7.0, 7.0), (7.5, 7.5), (8.0, 8.0), (8.5, 8.5), (9.0, 9.0), (9.5, 9.5), (10.0, 10.0), (10.5, 10.5), (11.0, 11.0), (11.5, 11.5), (12.0, 12.0)], help_text='Пример: 8.0, 8.5 ... 11.0', max_length=4, null=True, verbose_name='Размер перчаток')),
                ('shoe_size', models.IntegerField(blank=True, choices=[(35, '35'), (36, '36'), (37, '37'), (38, '38'), (39, '39'), (40, '40'), (41, '41'), (42, '42'), (43, '43'), (44, '44'), (45, '45'), (46, '46'), (47, '47'), (48, '48'), (49, '49'), (50, '50'), (51, '51'), (52, '52')], help_text='Пример: 35, 36 ... 52', null=True, verbose_name='Размер обуви')),
            ],
            options={
                'verbose_name': 'Сотрудник',
                'verbose_name_plural': 'Сотрудники',
                'ordering': ['last_name', 'first_name', 'patronymic'],
            },
        ),
        migrations.CreateModel(
            name='Item',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('item_type', models.CharField(help_text='Тип СИЗ, предмета', max_length=250, verbose_name='Тип')),
                ('item_name', models.CharField(help_text='Наименование СИЗ, предмета', max_length=250, verbose_name='Наименование')),
                ('item_lifespan', models.PositiveIntegerField(help_text='Срок годности (в месяцах)', verbose_name='Срок годности (в месяцах)')),
                ('item_size', models.CharField(max_length=100, verbose_name='Размер')),
                ('item_mu', models.CharField(choices=[('шт.', 'штук'), ('пар.', 'пар'), ('компл.', 'комплектов'), ('г.', 'грамм'), ('мл.', 'миллилитров')], default='шт.', max_length=10, verbose_name='Единица измерения')),
            ],
            options={
                'verbose_name': 'СИЗ',
                'verbose_name_plural': 'СИЗ',
            },
        ),
        migrations.CreateModel(
            name='Position',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position_name', models.CharField(max_length=100, unique=True, verbose_name='Название должности')),
            ],
            options={
                'verbose_name': 'Должность',
                'verbose_name_plural': 'Должности',
            },
        ),
        migrations.CreateModel(
            name='Issue',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, editable=False, verbose_name='Количество')),
                ('issue_date', models.DateField(help_text='Дата выдачи СИЗ сотруднику', verbose_name='Дата выдачи')),
                ('expiration_date', models.DateField(blank=True, help_text='Срок годности СИЗ', verbose_name='Срок годности до')),
                ('is_active', models.BooleanField(default=True, verbose_name='Активно (не списано)')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='core.Employee', verbose_name='Сотрудник')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='issues', to='core.Item', verbose_name='СИЗ')),
            ],
            options={
                'verbose_name': 'Выдача СИЗ',
                'verbose_name_plural': 'Выдачи СИЗ',
                'ordering': ['-issue_date'],
            },
        ),
        migrations.AddField(
            model_name='employee',
            name='position',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='employees', to='core.Position', verbose_name='Должность'),
        ),
        migrations.CreateModel(
            name='Norm',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('quantity', models.PositiveIntegerField(default=1, help_text='Сколько единиц СИЗ положено для этой должности', verbose_name='Количество')),
                ('item', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='norms', to='core.Item', verbose_name='СИЗ')),
                ('position', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='norms', to='core.Position', verbose_name='Должность')),
            ],
            options={
                'verbose_name': 'Норма выдачи',
                'verbose_name_plural': 'Нормы выдачи',
                'unique_together': {('position', 'item')},
            },
        ),
    ]
