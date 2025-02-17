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
    
    class Meta:
        verbose_name = "Сотрудник"
        verbose_name_plural = "Сотрудники"
        ordering = ["last_name", "first_name", "patronymic"]
    
    def issue_item(self, item, quantity=1, issue_date=None, expiration_date=None):
        """
        Выдает указанное количество СИЗ сотруднику.
        """
        if not issue_date:
            raise ValueError("Поле 'Дата выдачи' обязательно для заполнения.")
        
        for _ in range(quantity):
            Issue.objects.create(
                employee=self,
                item=item,
                issue_date=issue_date,
                expiration_date=expiration_date
            )
    
    def __str__(self):
        return f"{self.last_name} {self.first_name} {self.patronymic}".strip()

class Item(models.Model):
    MEASUREMENT_UNITS = (
        ("шт.", "штук"),
        ("пар.", "пар"),
        ("компл.", "комплектов"),
        ("г.", "грамм"),
        ("мл.", "миллилитров"),
    )
    
    item_type = models.CharField(
        "Тип СИЗ",
        max_length=250,
        help_text="Тип СИЗ"
    )
    item_name = models.CharField(
        "Наименование СИЗ",
        max_length=250,
    )
    item_lifespan = models.PositiveIntegerField(
        "Срок годности (в месяцах)",
        help_text="Срок годности (в месяцах)"
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
        verbose_name="Должность",
        related_name="norms"
    )
    item = models.ForeignKey(
        Item,
        on_delete=models.CASCADE,
        verbose_name="СИЗ",
        related_name="norms"
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        default=1,
        help_text="Сколько единиц СИЗ положено для этой должности"
    )

    class Meta:
        verbose_name = "Норма выдачи"
        verbose_name_plural = "Нормы выдачи"
        unique_together = [['position', 'item']]
    
    def get_remaining_quantity(self, employee):
        """
        Возвращает, сколько единиц СИЗ еще можно выдать сотруднику на этой должности.
        """
        if employee.position != self.position:
            return 0  # Норма не применяется к текущей должности
        active_issues_count = Issue.objects.filter(
            employee=employee,
            item=self.item,
            is_active=True
        ).count()
        return max(0, self.quantity - active_issues_count)
    
    def __str__(self):
        return f"{self.position}: {self.item} x{self.quantity}"

class Issue(models.Model):
    employee = models.ForeignKey(
        "Employee",
        on_delete=models.CASCADE,
        verbose_name="Сотрудник",
        related_name="issues"
    )
    item = models.ForeignKey(
        "Item",
        on_delete=models.CASCADE,
        verbose_name="СИЗ",
        related_name="issues"
    )
    quantity = models.PositiveIntegerField(
        "Количество",
        default=1,
        editable=False  # Запрещаем изменять вручную
    )
    issue_date = models.DateField(
        "Дата выдачи",
        blank=False,
        null=False,
        help_text="Дата выдачи СИЗ сотруднику"
    )
    expiration_date = models.DateField(
        "Срок годности до",
        blank=True,
        help_text="Срок годности СИЗ"
    )
    is_active = models.BooleanField(
        "Активно (не списано)",
        default=True
    )

    class Meta:
        verbose_name = "Выдача СИЗ"
        verbose_name_plural = "Выдачи СИЗ"
        ordering = ["-issue_date"]

    def __str__(self):
        status = "активно" if self.is_active else "списано"
        return f"{self.employee}: {self.item} ({status})"

    def clean(self):
        """
        Проверяет, не превышает ли выдача норму для должности.
        """
        if not self.is_active:
            return
        
        if not self.employee:
            raise ValidationError("Сотрудник не указан.")
        
        if not self.item:
            raise ValidationError("СИЗ не указано.")
        
        norm = Norm.objects.filter(
            position=self.employee.position,
            item=self.item
        ).first()

        if not norm:
            raise ValidationError(
                f"Для должности {self.employee.position} не задана норма по СИЗ {self.item}."
            )
        
        active_issues = Issue.objects.filter(
            employee=self.employee,
            item=self.item,
            is_active=True
        ).exclude(pk=self.pk)

        if active_issues.count() + 1 > norm.quantity:
            raise ValidationError(
                f"Превышена норма. Доступно к выдаче: {norm.quantity - active_issues.count()} ед."
            )
        
    def save(self, *args, **kwargs):
        if not self.issue_date:
            raise ValidationError("Поле 'Дата выдачи' обязательно для заполнения.")
        
        if not self.expiration_date and self.item:
            self.expiration_date = self.issue_date + relativedelta(months=self.item.item_lifespan)
        

    def save(self, *args, **kwargs):
        if not self.issue_date:
            raise ValidationError("Поле 'Дата выдачи' обязательно для заполнения.")

        # Рассчитываем срок годности, если он не задан
        if not self.expiration_date and self.item:
            self.expiration_date = self.issue_date + relativedelta(months=self.item.item_lifespan)

        self.clean()
        super().save(*args, **kwargs)
