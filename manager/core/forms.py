from django import forms
from .models import Employee

from django import forms
from .models import Employee, Position

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
