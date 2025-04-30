from django.contrib.auth.models import AbstractUser
from django.db import models

class CustomUser(AbstractUser):
    patronymic = models.CharField(
        max_length=150,
        verbose_name='Отчество'
    )
    position = models.CharField(
        max_length=200,
        verbose_name='Должность ответственного за выдачу СИЗ')
    department = models.CharField(
        max_length=100,
        verbose_name='Подразделение')
    last_activity = models.DateTimeField(
        auto_now=True,
        verbose_name='Последняя активность')
