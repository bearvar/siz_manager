# users/views.py
# Импортируем CreateView, чтобы создать ему наследника
from django.views.generic import CreateView, TemplateView
from django.contrib.auth.views import (LogoutView, LoginView,
        PasswordChangeView, PasswordChangeDoneView,
        PasswordResetView, PasswordResetDoneView,
        PasswordResetConfirmView, PasswordResetCompleteView)
from django.contrib.auth.decorators import login_required

# Функция reverse_lazy позволяет получить URL по параметрам функции path()
# Берём, тоже пригодится
from django.urls import reverse_lazy

# Импортируем класс формы, чтобы сослаться на неё во view-классе
from .forms import CreationForm


class SignUp(CreateView):
    form_class = CreationForm
    # После успешной регистрации перенаправляем пользователя на главную.
    success_url = reverse_lazy('users:registration_success')
    template_name = 'users/signup.html'

class RegistrationSuccessView(TemplateView):
    template_name = 'users/registration_success.html'

#@login_required
class ChangePassword(PasswordChangeView):
    success_url = reverse_lazy('users:password_change_done')
    template_name = 'users/password_change_form.html'
