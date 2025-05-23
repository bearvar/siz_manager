from django import forms
from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Employee, Position, Norm, Issue, PPEType, NormHeight, HeightGroup, FlushingAgentNorm, FlushingAgentType, FlushingAgentIssue


class EmployeeForm(forms.ModelForm):
    height_group = forms.ModelChoiceField(
        queryset=HeightGroup.objects.all(),
        required=False,
        label="Группа работ на высоте",
        help_text="Выберите группу безопасности для высотных работ",
        widget=forms.Select(attrs={'class': 'form-control'}))
    
    class Meta:
        model = Employee
        fields = [
            'last_name', 
            'first_name', 
            'patronymic', 
            'position', 
            'department',
            'height_group',  # Добавляем новое поле
            'body_size', 
            'head_size', 
            'glove_size', 
            'shoe_size'
        ]
        widgets = {
            'position': forms.Select(attrs={'class': 'form-control'}),
            'height_group': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['height_group'].queryset = HeightGroup.objects.all().order_by('level')
        self.fields['height_group'].empty_label = "Не выбрано"
        self.fields['height_group'].label_from_instance = lambda obj: f"Группа {obj.level}"


class PositionForm(forms.ModelForm):
    class Meta:
        model = Position
        fields = ['position_name']


class NormCreateForm(forms.ModelForm):
    ppe_type_name = forms.CharField(
        label="Тип СИЗ",
        help_text="Введите название типа СИЗ",
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

class FlushingNormCreateForm(forms.ModelForm):
    position = forms.ModelChoiceField(
        queryset=Position.objects.all(),
        label="Должность",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    agent_type_name = forms.CharField(
        label="Тип смывочного средства",
        help_text="Введите название типа средства. Пример: 'Мыло жидкое', 'Спрей от кровососущих насекомых'",
        max_length=255)
    monthly_ml = forms.IntegerField(
        label="Норма в месяц (мл)",
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'step': 1}))

    class Meta:
        model = FlushingAgentNorm
        fields = ['monthly_ml']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['position'].empty_label = "Выберите должность"

    def clean_agent_type_name(self):
        agent_type_name = self.cleaned_data['agent_type_name'].strip()
        if not agent_type_name:
            raise ValidationError("Название типа средства обязательно")
        return agent_type_name

    def clean(self):
        cleaned_data = super().clean()
        position = cleaned_data.get('position')
        agent_type_name = cleaned_data.get('agent_type_name')

        if position and agent_type_name:
            normalized_name = agent_type_name.strip().capitalize()
            
            try:
                agent_type = FlushingAgentType.objects.get(name__iexact=normalized_name)
                if FlushingAgentNorm.objects.filter(position=position, agent_type=agent_type).exists():
                    self.add_error(
                        'agent_type_name',
                        f"Норма для '{agent_type.name}' уже существует для этой должности"
                    )
                else:
                    cleaned_data['agent_type'] = agent_type
            except FlushingAgentType.DoesNotExist:
                cleaned_data['new_agent_type'] = normalized_name

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.position = self.cleaned_data['position']
        
        agent_type_name = self.cleaned_data.get('agent_type_name').strip().capitalize()
        
        if 'agent_type' in self.cleaned_data:
            instance.agent_type = self.cleaned_data['agent_type']
        else:
            instance.agent_type = FlushingAgentType.objects.create(
                name=agent_type_name)
        
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

    issue_date = forms.DateField(
        label="Дата выдачи",
        input_formats=['%d.%m.%Y'],
        widget=forms.DateInput(
            format='%d.%m.%Y',
            attrs={
                'class': 'form-control',
                'placeholder': 'дд.мм.гггг',
                'type': 'text'
            }
        )
    )

    class Meta:
        model = Issue
        fields = ['ppe_type', 'item_name', 'issue_date', 'item_size']
        # widgets = {
        #     'issue_date': forms.DateInput(attrs={'type': 'date'}),
        # }

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee')
        super().__init__(*args, **kwargs)
        
        # Инициализируем QuerySet'ы
        position_ppe = PPEType.objects.none()
        height_ppe = PPEType.objects.none()
        
        # Для должности
        if self.employee.position:
            position_ppe = PPEType.objects.filter(
                norms__position=self.employee.position
            ).distinct()
            
        # Для высотной группы
        if self.employee.height_group:
            height_ppe = PPEType.objects.filter(
                height_norms__height_group=self.employee.height_group
            ).distinct()
        
        # Объединяем и исключаем дубликаты
        combined_ppe = (position_ppe | height_ppe).distinct()
        
        self.fields['ppe_type'].queryset = combined_ppe
        self.fields['ppe_type'].widget.attrs.update({'class': 'form-select'})
        self.fields['ppe_type'].empty_label = "Выберите тип СИЗ"
        self.fields['ppe_type'].help_text = "Выберите из норм должности или высотных работ"


class FlushingAgentIssueForm(forms.ModelForm):
    agent_type = forms.ModelChoiceField(
        label="Тип средства",
        queryset=FlushingAgentType.objects.none()
    )
    item_name = forms.CharField(
        label="Название средства",
        max_length=255,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Например: Мыло жидкое "Clean", Спрей Mosquitall'
        })
    )
    volume_ml_nominal = forms.IntegerField(
        label="Номинальный объем (мл)",
        min_value=1,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,
            'step': 1
        })
    )
    issue_date = forms.DateField(
        label="Дата выдачи",
        input_formats=['%d.%m.%Y'],
        widget=forms.DateInput(
            format='%d.%m.%Y',
            attrs={
                'class': 'form-control',
                'placeholder': 'дд.мм.гггг',
                'type': 'text'
            }
        )
    )

    class Meta:
        model = FlushingAgentIssue
        fields = ['agent_type', 'item_name', 'volume_ml_nominal', 'issue_date']
        labels = {
            'item_name': 'Конкретное название средства',
            'volume_ml_nominal': 'Объем флакона (мл)'
        }
        widgets = {
            'agent_type': forms.Select(attrs={'class': 'form-select'}),
            'volume_ml_nominal': forms.NumberInput(attrs={'class': 'form-control'})
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.employee = self.employee
        instance.volume_ml = self.cleaned_data['volume_ml_nominal']  # Set initial volume
        if commit:
            instance.save()
        return instance

    def __init__(self, *args, **kwargs):
        self.employee = kwargs.pop('employee', None)
        super().__init__(*args, **kwargs)
        
        if self.employee and self.employee.position:
            # Get agent types from norms for this position
            norms = FlushingAgentNorm.objects.filter(position=self.employee.position)
            self.fields['agent_type'].queryset = FlushingAgentType.objects.filter(
                id__in=norms.values_list('agent_type', flat=True)
            ).distinct().order_by('name')
            self.fields['agent_type'].empty_label = "Выберите средство"
            self.fields['agent_type'].label_from_instance = lambda obj: obj.name
        else:
            self.fields['agent_type'].queryset = FlushingAgentType.objects.none()
            self.fields['agent_type'].empty_label = "Нет доступных средств"


class NormHeightCreateForm(forms.ModelForm):
    ppe_type_name = forms.CharField(
        label="Тип СИЗ",
        help_text="Введите название типа СИЗ",
        max_length=255
    )
    quantity = forms.IntegerField(
        label="Количество",
        min_value=1,
        initial=1,
        required=True
    )
    lifespan = forms.IntegerField(
        label="Срок годности (месяцев)",
        min_value=1,
        initial=6,
        required=True
    )

    class Meta:
        model = NormHeight  # Явно указываем модель
        fields = ['quantity', 'lifespan']
        labels = {
            'quantity': 'Количество',
            'lifespan': 'Срок годности (месяцев)',
        }

    def __init__(self, *args, **kwargs):
        self.height_group = kwargs.pop('height_group', None)
        super().__init__(*args, **kwargs)
        self.fields['ppe_type_name'].required = True

    def clean_ppe_type_name(self):
        ppe_type_name = self.cleaned_data['ppe_type_name'].strip()
        if not ppe_type_name:
            raise ValidationError("Название типа СИЗ обязательно для заполнения")
        return ppe_type_name

    def clean(self):
        cleaned_data = super().clean()
        ppe_type_name = cleaned_data.get('ppe_type_name')
        
        normalized_name = ppe_type_name.strip().capitalize()
        
        try:
            ppe_type = PPEType.objects.get(name__iexact=normalized_name)
            if NormHeight.objects.filter(height_group=self.height_group, ppe_type=ppe_type).exists():
                self.add_error('ppe_type_name', 
                    f"Тип СИЗ '{ppe_type.name}' уже добавлен для этой группы")
            else:
                cleaned_data['ppe_type'] = ppe_type
        except PPEType.DoesNotExist:
            cleaned_data['new_ppe_type'] = normalized_name

        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.height_group = self.height_group

        # Создаем или получаем тип СИЗ
        ppe_type_name = self.cleaned_data['ppe_type_name'].strip().capitalize()
        ppe_type, created = PPEType.objects.get_or_create(name=ppe_type_name)
        instance.ppe_type = ppe_type

        if commit:
            instance.save()
        return instance
    

class SAPImportForm(forms.Form):
    sap_file = forms.FileField(
        label='Файл SAP',
        help_text='Выберите файл в формате CSV/XLSX для импорта'
    )


class EmployeeImportItemsForm(forms.Form):
    sap_file = forms.FileField(
        label='Файл SAP',
        help_text='Выберите файл в формате CSV/XLSX для импорта предметов'
    )
