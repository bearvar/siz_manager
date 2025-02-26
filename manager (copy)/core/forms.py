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
    ppe_type_name = forms.CharField(
        label="Тип СИЗ",
        help_text="Введите название существующего типа или создайте новый",
        max_length=255
    )

    class Meta:
        model = Norm
        fields = ['quantity', 'lifespan']
        labels = {
            'quantity': 'Количество',
            'lifespan': 'Срок годности (месяцев)',
        }

    def __init__(self, *args, **kwargs):
        self.position = kwargs.pop('position', None)
        super().__init__(*args, **kwargs)
        
        if self.instance.pk and self.instance.ppe_type:
            self.fields['ppe_type_name'].initial = self.instance.ppe_type.name

    def clean_ppe_type_name(self):
        ppe_type_name = self.cleaned_data['ppe_type_name'].strip()
        if not ppe_type_name:
            raise ValidationError("Название типа СИЗ обязательно для заполнения")
        return ppe_type_name

    def clean(self):
        cleaned_data = super().clean()
        ppe_type_name = cleaned_data.get('ppe_type_name')
        
        if not ppe_type_name:
            return  # Ошибка уже обработана в clean_ppe_type_name

        normalized_name = ppe_type_name.capitalize()
        
        try:
            # Ищем существующий тип (без учета регистра)
            ppe_type = PPEType.objects.get(name__iexact=normalized_name)
            
            # Проверяем дубликат для текущей должности
            if Norm.objects.filter(position=self.position, ppe_type=ppe_type).exists():
                self.add_error(
                    'ppe_type_name',
                    f"Тип СИЗ '{ppe_type.name}' уже добавлен для этой должности"
                )
            else:
                cleaned_data['ppe_type'] = ppe_type
                
        except PPEType.DoesNotExist:
            # Создаем новый тип СИЗ
            cleaned_data['new_ppe_type'] = normalized_name

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.position = self.position
        
        ppe_type = self.cleaned_data.get('ppe_type')
        new_ppe_type = self.cleaned_data.get('new_ppe_type')
        
        if new_ppe_type:
            ppe_type, created = PPEType.objects.get_or_create(name=new_ppe_type)
        
        if not ppe_type:
            raise ValueError("Не удалось определить тип СИЗ")
            
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
    item_name = forms.CharField(
        label="Наименование предмета",
        max_length=255,
        help_text="Наименование СИЗ"
    )

    class Meta:
        model = Issue
        fields = ['ppe_type', 'item_name', 'issue_date', 'item_size']
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