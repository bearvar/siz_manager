from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import (
    UserCreationForm, PasswordChangeForm, PasswordResetForm, SetPasswordForm
)

User = get_user_model()


# класс для формы регистрации
class CreationForm(UserCreationForm):
    first_name = forms.CharField(label="Имя")
    last_name = forms.CharField(label="Фамилия")
    patronymic = forms.CharField(label="Отчество", required=False)
    username = forms.CharField(label="Имя пользователя")
    email = forms.EmailField(label="Электронная почта")
    position = forms.CharField(label="Должность")
    department = forms.CharField(label="Подразделение")

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ('last_name', 'first_name', 'patronymic', 'username', 'email', 'position', 'department')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].label = "Пароль"
        self.fields['password1'].help_text = " * Ваш пароль не должен быть слишком похож на другую вашу личную информацию.<br> * Ваш пароль должен содержать не менее 8 символов.<br> * Ваш пароль не должен быть общеиспользуемым паролем.<br> * Ваш пароль не должен состоять только из цифр."
        self.fields['password2'].label = "Подтверждение пароля"
        self.fields['password2'].help_text = " * Введите пароль еще раз, для подтверждения."

class CustomPasswordChangeForm(PasswordChangeForm):
    old_password = forms.CharField(
        label="Старый пароль",
        widget=forms.PasswordInput(attrs={'autocomplete': 'current-password', 'class': 'form-control'})
    )
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'}),
        help_text="""<ul>
            <li>Ваш пароль не должен быть слишком похож на другую личную информацию.</li>
            <li>Пароль должен содержать не менее 8 символов.</li>
            <li>Не используйте общераспространенные пароли.</li>
            <li>Пароль не может состоять только из цифр.</li>
        </ul>"""
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password', 'class': 'form-control'})
    )

class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        label="Электронная почта",
        widget=forms.EmailInput(attrs={'class': 'form-control'})
    )

class CustomSetPasswordForm(SetPasswordForm):
    new_password1 = forms.CharField(
        label="Новый пароль",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password2 = forms.CharField(
        label="Подтверждение нового пароля",
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )