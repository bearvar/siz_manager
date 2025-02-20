from django import forms
from .models import Employee

from django import forms
from .models import Employee, Position, Norm, Item

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
    class Meta:
        model = Norm
        fields = ['item_type', 'quantity']
        labels = {
            'item_type': 'Тип СИЗ',
            'quantity': 'Количество'
        }
        help_texts = {
            'item_type': 'Укажите тип СИЗ',
            'quantity': 'Укажите количество для выдачи'
        },
        
    def clean(self):
        cleaned_data = super().clean()
        item_type = cleaned_data.get("item_type")

        # Проверяем, существует ли уже норма с таким типом СИЗ для данной должности
        if self._meta.model.objects.filter(position=self.instance.position, item_type=item_type).exists():
            raise forms.ValidationError(
                "Уже существует норма с таким типом СИЗ для данной должности."
            )

        return cleaned_data
