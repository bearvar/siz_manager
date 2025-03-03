from django.db import models
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta
from django.db.models.signals import post_migrate
from django.dispatch import receiver
import math

MEASUREMENT_UNITS = (
    ("шт.", "штук"),
    ("пар.", "пар"),
    ("компл.", "комплектов"),
    ("г.", "грамм"),
    ("мл.", "миллилитров"),
)

class Position(models.Model):
    position_name = models.CharField(
        "Название должности",
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = "Должность"
        verbose_name_plural = "Должности"
    
    def __str__(self):
        return self.position_name


class PPEType(models.Model):
    name = models.CharField(
        "Тип СИЗ",
        max_length=255,
        unique=True,
        help_text="Укажите тип средства индивидуальной защиты"
    )
    default_mu = models.CharField(
        "Единица измерения",
        max_length=10,
        choices=MEASUREMENT_UNITS,  # Используем константы из Issue
        default="шт."
    )
    
    class Meta:
        verbose_name = "Тип СИЗ"
        verbose_name_plural = "Типы СИЗ"
        ordering = ['name']

    def __str__(self):
        return self.name


class HeightGroup(models.Model):
    level = models.PositiveIntegerField(
        "Уровень",
        unique=True,
        choices=[(1, '1 группа'), (2, '2 группа'), (3, '3 группа')]
    )

    class Meta:
        verbose_name = "Группа работ на высоте"
        verbose_name_plural = "Группы работ на высоте"
        ordering = ['level']

    def __str__(self):
        return f"Группа {self.level}"
    
    @classmethod
    def ensure_groups_exist(cls):
        """Создает группы, если они отсутствуют"""
        for level in [1, 2, 3]:
            cls.objects.get_or_create(level=level)
            
    def save(self, *args, **kwargs):
        # Запрещаем создание новых групп
        if self.pk is None and self.level not in [1, 2, 3]:
            raise ValueError("Можно создавать только группы 1, 2 и 3 уровня")
        super().save(*args, **kwargs)


class NormHeight(models.Model):
    height_group = models.ForeignKey(
        HeightGroup,
        on_delete=models.CASCADE,
        related_name='norms'
    )
    ppe_type = models.ForeignKey(
        PPEType,
        on_delete=models.CASCADE,
        related_name='height_norms'
    )
    quantity = models.PositiveIntegerField("Количество")
    lifespan = models.PositiveIntegerField(
        "Срок годности (месяцев)",
        default=6  # По умолчанию меньше чем для обычных норм
    )

    class Meta:
        unique_together = ['height_group', 'ppe_type']
        verbose_name = "Норма для высотных работ"
        verbose_name_plural = "Нормы для высотных работ"

    def __str__(self):
        return f"{self.height_group}: {self.ppe_type} x{self.quantity}"



class ConsumableGroup(models.Model):
    group_name = models.CharField(
        "Название группы расходников",
        max_length=100,
        unique=True
    )
    
    class Meta:
        verbose_name = "Группа расходников"
        verbose_name_plural = "Группы расходников"
    
    def __str__(self):
        return self.group_name

class NormConsumable(models.Model):
    consumable_group = models.ForeignKey(
        ConsumableGroup,
        on_delete=models.CASCADE,
        related_name='norms'
    )
    consumable_type = models.CharField(
        "Тип расходника",
        max_length=255
    )
    quantity = models.FloatField(
        "Расход в месяц",
        help_text="Количество расходуемого материала в месяц"
    )
    mu = models.CharField(
        "Единица измерения",
        max_length=10,
        choices=MEASUREMENT_UNITS,
        default="мл."
    )

    class Meta:
        unique_together = ['consumable_group', 'consumable_type']
        verbose_name = "Норма расходников"
        verbose_name_plural = "Нормы расходников"

    def __str__(self):
        return f"{self.consumable_group}: {self.consumable_type} - {self.quantity}{self.mu}/мес"



class ConsumableIssue(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='consumable_issues'
    )
    norm = models.ForeignKey(
        NormConsumable,
        on_delete=models.CASCADE,
        verbose_name="Норма расхода"
    )
    initial_quantity = models.FloatField("Выданное количество")
    issue_date = models.DateField("Дата выдачи")
    is_active = models.BooleanField("Активно", default=True)

    @property
    def depletion_date(self):
        """Точная дата окончания запасов"""
        if self.norm.quantity <= 0:
            return None
        months_needed = math.ceil(self.initial_quantity / self.norm.quantity)
        return self.issue_date + relativedelta(months=months_needed)

    def get_remaining_as_of(self, target_date):
        """Остаток на конкретную дату с учетом расходов"""
        if target_date < self.issue_date:
            return self.initial_quantity
            
        if self.depletion_date and target_date >= self.depletion_date:
            return 0.0

        full_months = (target_date.year - self.issue_date.year) * 12 + (target_date.month - self.issue_date.month)
        if target_date.day < self.issue_date.day:
            full_months -= 1

        consumed = self.norm.quantity * full_months
        return max(self.initial_quantity - consumed, 0)

    def update_status(self):
        """Обновление статуса с учетом текущей даты"""
        if self.get_remaining_as_of(date.today()) <= 0:
            self.is_active = False
            self.save()



class Employee(models.Model):
    # Существующие поля
    first_name = models.CharField("Имя", max_length=50)
    last_name = models.CharField("Фамилия", max_length=50)
    patronymic = models.CharField("Отчество", max_length=50)
    position = models.ForeignKey(
        Position,
        on_delete=models.SET_NULL,
        verbose_name="Должность",
        null=True,
        related_name="employees"
    )
    height_group = models.ForeignKey(
        HeightGroup,
        on_delete=models.SET_NULL,
        verbose_name="Группа работ на высоте",
        null=True,
        blank=True
    )
    consumable_group = models.ForeignKey(
        ConsumableGroup,
        on_delete=models.SET_NULL,
        verbose_name="Группа расходников",
        null=True,
        blank=True
    )
    department = models.CharField("Подразделение", max_length=50)
    
    BODY_SIZE_CHOICES = [
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
    ]
    
    HEAD_SIZE_CHOICES = [
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
    ]
    
    GLOVE_SIZE_CHOICES = [
        (6.0, "6.0"),
        (6.5, "6.5"), 
        (7.0, "7.0"),
        (7.5, "7.5"),
        (8.0, "8.0"),
        (8.5, "8.5"),
        (9.0, "9.0"),
        (9.5, "9.5"),
        (10.0, "10.0"),
        (10.5, "10.5"),
        (11.0, "11.0"),
        (11.5, "11.5"),
        (12.0, "12.0")
    ]
    
    SHOE_SIZE_CHOICES = [(i, str(i)) for i in range(35, 53)]  # 35-52
    
    body_size = models.CharField(
        "Размер спецодежды (тело)",
        max_length=40,
        choices=BODY_SIZE_CHOICES,
        blank=True,
        null=True,
        help_text="Пример: 44-46/158-164"
    )
    
    head_size = models.CharField(
        "Размер головного убора",
        max_length=3,
        choices=HEAD_SIZE_CHOICES,
        blank=True,
        null=True,
        help_text="Пример: 56, 57, 58"
    )
    
    glove_size = models.FloatField(
        "Размер перчаток",
        choices=GLOVE_SIZE_CHOICES,
        blank=True,
        null=True,
        help_text="Пример: 8.0, 8.5 ... 11.0"
    )
    
    shoe_size = models.IntegerField(
        "Размер обуви",
        choices=SHOE_SIZE_CHOICES,
        blank=True,
        null=True,
        help_text="Пример: 35, 36 ... 52"
    )
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["last_name", "first_name", "patronymic"]
    
    def issue_item(self, item_type, quantity=1, issue_date=None, expiration_date=None):
        """
        Выдает указанное количество СИЗ сотруднику.
        """
        if not issue_date:
            raise ValueError("Поле 'Дата выдачи' обязательно для заполнения.")
        
        for _ in range(quantity):
            Issue.objects.create(
                employee=self,
                item_type=item_type,
                issue_date=issue_date,
                expiration_date=expiration_date
            )
    
    def clean(self):
        if self.height_group and not self.position:
            raise ValidationError(
                {'height_group': 'Для назначения группы высоты требуется указать должность'}
            )
        super().clean()
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()


class Norm(models.Model):
    position = models.ForeignKey(
        Position,
        on_delete=models.CASCADE,
        related_name='norms'
    )
    ppe_type = models.ForeignKey(
        PPEType,
        on_delete=models.CASCADE,
        related_name='norms'
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        help_text="Сколько единиц СИЗ положено для этой должности"
    )
    lifespan = models.PositiveIntegerField(
        "Срок годности (месяцев)",
        default=12
    )

    class Meta:
        unique_together = ['position', 'ppe_type']
        verbose_name = "Норма выдачи"
        verbose_name_plural = "Нормы выдачи"
    
    def __str__(self):
        return f"{self.position}: {self.ppe_type} x{self.quantity}"
    
    def active_issues(self, employee):
        return Issue.objects.filter(
            employee=employee,
            ppe_type=self.ppe_type,
            is_active=True
        )


class Issue(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        related_name='issues'
    )
    ppe_type = models.ForeignKey(
        PPEType,
        on_delete=models.CASCADE,
        verbose_name="Тип СИЗ",
        related_name='issues'
    )
    item_name = models.CharField(
        "Наименование предмета",
        max_length=255,
        help_text="Наименование предмета СИЗ"
    )
    issue_date = models.DateField(
        "Дата выдачи"
    )
    expiration_date = models.DateField(
        "Срок годности",
        blank=True,
        null=True
    )
    is_active = models.BooleanField(
        "Активно",
        default=True
    )
    item_size = models.CharField(
        "Размер",
        max_length=100,
        blank=True,
        null=True,
        help_text="Укажите размер если есть (например, 42, L, 10.5)"
    )
    item_mu = models.CharField(
        "Единица измерения",
        max_length=10,
        choices=MEASUREMENT_UNITS,
        default="шт."
    )
    
    def save(self, *args, **kwargs):
        # Если дата списания была изменена вручную - сохраняем как есть
        if self.expiration_date != self._original_expiration_date:
            super().save(*args, **kwargs)
            return
        
        # Пересчет только если:
        # - дата выдачи изменилась ИЛИ
        # - срок списания не задан
        if self.issue_date != self._original_issue_date or not self.expiration_date:
            # Сбрасываем для пересчета
            self.expiration_date = None
            
            # Приоритет для высотных норм
            if self.employee.height_group:
                try:
                    norm = NormHeight.objects.get(
                        height_group=self.employee.height_group,
                        ppe_type=self.ppe_type
                    )
                    self.expiration_date = self.issue_date + relativedelta(months=norm.lifespan)
                except NormHeight.DoesNotExist:
                    pass
            
            # Если не нашли, проверяем обычные нормы
            if not self.expiration_date and self.employee.position:
                try:
                    norm = Norm.objects.get(
                        position=self.employee.position,
                        ppe_type=self.ppe_type
                    )
                    self.expiration_date = self.issue_date + relativedelta(months=norm.lifespan)
                except Norm.DoesNotExist:
                    pass
        
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Работник: {self.employee}; Тип СИЗ: {self.ppe_type}; Название: {self.item_name}; Дата выдачи: {self.issue_date}"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_issue_date = self.issue_date
        self._original_expiration_date = self.expiration_date


@receiver(post_migrate)
def create_initial_groups(sender, **kwargs):
    if sender.name == 'core':
        from .models import HeightGroup
        HeightGroup.ensure_groups_exist()