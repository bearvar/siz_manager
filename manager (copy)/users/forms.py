from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model


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
