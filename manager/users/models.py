from django.contrib.auth.models import AbstractUser
from django.db import models

from .theme import THEME_CHOICES, THEME_LIGHT


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
    theme = models.CharField(
        max_length=10,
        choices=THEME_CHOICES,
        default=THEME_LIGHT,
        verbose_name='Тема интерфейса')
