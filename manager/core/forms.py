from django import forms
from django.core.exceptions import ValidationError
from .models import Employee

from django import forms
from .models import Employee, Position, Norm, Issue, PPEType

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['last_name', 'first_name', 'patronymic', 'position', 'department', 'body_size', 'head_size', 'glove_size', 'shoe_size']
        widgets = {
            'position': forms.Select(attrs={'class': 'form-control'})
        }

class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['position_name']

class NormCreateForm(forms.ModelForm):
    new_ppe_type = forms.CharField(
        label="Новый тип СИЗ",
        required=False,
        help_text="Введите название нового типа",
        max_length=255
    )

    class Meta:
        model = Norm
        fields = ['ppe_type', 'quantity']
        labels = {
            'ppe_type': 'Существующий тип СИЗ',
            'quantity': 'Количество'
        }

    def __init__(self, *args, **kwargs):
        self.position = kwargs.pop('position', None)
        super().__init__(*args, **kwargs)
        self.fields['ppe_type'].queryset = PPEType.objects.exclude(
            norms__position=self.position
        )
        self.fields['ppe_type'].required = False

    def clean(self):
        cleaned_data = super().clean()
        ppe_type = cleaned_data.get('ppe_type')
        new_ppe_type = cleaned_data.get('new_ppe_type')

        if not ppe_type and not new_ppe_type:
            raise ValidationError("Необходимо выбрать тип СИЗ или ввести новый")

        if ppe_type and new_ppe_type:
            raise ValidationError("Выберите только один вариант: существующий тип или новый")

        if new_ppe_type:
            # Проверяем не существует ли уже такого типа
            if PPEType.objects.filter(name__iexact=new_ppe_type.strip()).exists():
                raise ValidationError("Такой тип СИЗ уже существует")
            
            # Проверяем не добавлен ли уже такой тип для этой должности
            if Norm.objects.filter(
                position=self.position,
                ppe_type__name__iexact=new_ppe_type.strip()
            ).exists():
                raise ValidationError("Этот тип СИЗ уже добавлен для данной должности")

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.position = self.position
        
        new_type = self.cleaned_data.get('new_ppe_type')
        if new_type:
            ppe_type, created = PPEType.objects.get_or_create(
                name=new_type.strip()
            )
            instance.ppe_type = ppe_type

        if commit:
            instance.save()
        return instance


class IssueCreateForm(forms.ModelForm):
    quantity = forms.IntegerField(
        min_value=1,
        initial=1,
        label="Количество для выдачи"
    )
    item_size = forms.CharField(
        label="Размер",
        max_length=100,
        required=False,
        help_text="Укажите размер (например, 42, L, 10.5)"
    )

    class Meta:
        model = Issue
        fields = ['ppe_type', 'issue_date', 'item_size']  # Убрали expiration_date
        widgets = {
            'issue_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee')
        super().__init__(*args, **kwargs)
        
        # Фильтруем типы СИЗ по нормам должности
        self.fields['ppe_type'].queryset = PPEType.objects.filter(
            norms__position=self.employee.position
        ).distinct()
        
        # Настройка полей
        self.fields['ppe_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['ppe_type'].empty_label = "Выберите тип СИЗ"