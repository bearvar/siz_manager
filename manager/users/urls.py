from argparse import Namespace
from django.urls import path
from django.contrib.auth.views import (LogoutView, LoginView,
        PasswordChangeDoneView, PasswordResetView, PasswordResetDoneView,
        PasswordResetConfirmView, PasswordResetCompleteView)
from . import views

from django.views import View
from django.http import HttpResponseRedirect
from django.urls import reverse_lazy
from .forms import CreationForm, CustomPasswordChangeForm, CustomPasswordResetForm, CustomSetPasswordForm


app_name = 'users'

class LogoutViewGet(LogoutView):

    def dispatch(self, request, *args, **kwargs):
        if self.request.method == 'GET':
            return self.post(request, *args, **kwargs)
        return super().dispatch(request, *args, **kwargs)

urlpatterns = [
    # Полный адрес страницы регистрации - auth/signup/,
    # но префикс auth/ обрабатывется в головном urls.py
    path('signup/', views.SignUp.as_view(), name='signup'),
    path(
        'registration_success/',
        views.RegistrationSuccessView.as_view(),
        name='registration_success'),
    path(
        'logout/',
        LogoutViewGet.as_view(template_name='users/logged_out.html'),
        name='logout'
    ),
    path(
        'login/',
        LoginView.as_view(template_name='users/login.html'),
        name='login'
    ),
    path(
        'password_change/',
        views.ChangePassword.as_view(
            template_name='users/password_change_form.html'
        ),
        name='password_change'
    ),
    path(
        'password_change/done/',
        PasswordChangeDoneView.as_view(
            template_name='users/password_change_done.html'),
        name='password_change_done'
    ),
    path(
        'password_reset/',
        PasswordResetView.as_view(
            template_name='users/password_reset_form.html',
            form_class=CustomPasswordResetForm
        ),
        name='password_reset_form'
    ),
    path(
        'password_reset/done/',
        PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html'),
        name='password_reset_done'
    ),
    path(
        'reset/<uidb64>/<token>/',
        PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
            form_class=CustomSetPasswordForm
        ),
        name='password_reset_confirm'
    ),
    path(
        'reset/done/',
        PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html'),
        name='password_reset_complete'
    ),
]
