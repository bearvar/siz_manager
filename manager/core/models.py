from django.db import models
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta

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
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

    # Логика не финальная
    def get_position_change_report(self, new_position):
        """
        Возвращает отчет о необходимых изменениях при переводе на новую должность.
        Формат:
        {
            "to_remove": {item: количество_к_списанию},
            "to_issue": {item: количество_к_выдаче}
        }
        """
        # Текущие активные выдачи сотрудника
        current_issues = self.issues.filter(is_active=True)
        
        # Нормы для новой должности
        new_norms = Norm.objects.filter(position=new_position)
        
        # СИЗ, которые должны быть у сотрудника по новой должности
        required_items = {norm.item: norm.quantity for norm in new_norms}
        
        # СИЗ, которые есть у сотрудника сейчас
        current_items = {}
        for issue in current_issues:
            current_items[issue.item] = current_items.get(issue.item, 0) + 1
        
        # Определяем избыточные СИЗ
        items_to_remove = {}
        for item, count in current_items.items():
            required_count = required_items.get(item, 0)
            if count > required_count:
                items_to_remove[item] = count - required_count
        
        # Определяем недостающие СИЗ
        items_to_add = {}
        for item, required_count in required_items.items():
            current_count = current_items.get(item, 0)
            if required_count > current_count:
                items_to_add[item] = required_count - current_count
        
        return {
            "to_remove": items_to_remove,
            "to_issue": items_to_add
        }

class PPEType(models.Model):
    name = models.CharField(
        "Тип СИЗ",
        max_length=255,
        unique=True,
        help_text="Укажите тип средства индивидуальной защиты"
    )
    
    class Meta:
        verbose_name = "Тип СИЗ"
        verbose_name_plural = "Типы СИЗ"
        ordering = ['name']

    def __str__(self):
        return self.name

class Item(models.Model):
    MEASUREMENT_UNITS = (
        ("шт.", "штук"),
        ("пар.", "пар"),
        ("компл.", "комплектов"),
        ("г.", "грамм"),
        ("мл.", "миллилитров"),
    )
    ppe_type = models.ForeignKey(
        PPEType,
        on_delete=models.CASCADE,
        related_name='items',
        verbose_name="Тип СИЗ"
    )
    item_name = models.CharField(
        "Наименование",
        max_length=250,
        help_text="Наименование СИЗ, предмета"
    )
    item_lifespan = models.PositiveIntegerField(
        "Срок годности (в месяцах)",
        help_text="Срок годности (в месяцах)"
    )
    item_size = models.CharField(
        "Размер",
        max_length=100,
    )
    item_mu = models.CharField(
        "Единица измерения",
        max_length=10,
        choices=MEASUREMENT_UNITS,
        default="шт."
    )
    
    class Meta:
        verbose_name = "СИЗ"
        verbose_name_plural = "СИЗ"
    
    def __str__(self):
        return f"{self.item_name}, ({self.get_item_mu_display()})"

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

    class Meta:
        unique_together = ['position', 'ppe_type']
        verbose_name = "Норма выдачи"
        verbose_name_plural = "Нормы выдачи"
    
    def __str__(self):
        return f"{self.position}: {self.item_type} x{self.quantity}"


class Issue(models.Model):
    employee = models.ForeignKey(
        Employee, 
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        related_name='issues'
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        related_name='issues',
        verbose_name="СИЗ"
    )
    issue_date = models.DateField(
        "Дата выдачи",
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

    def save(self, *args, **kwargs):
        if not self.expiration_date and self.item.item_lifespan:
            self.expiration_date = self.issue_date + relativedelta(months=self.item.item_lifespan)
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.employee} - {self.item} ({self.issue_date})"