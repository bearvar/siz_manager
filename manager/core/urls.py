from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('position/create/', views.position_create, name='position_create'),
    path('norm/create/<int:position_id>/', views.create_norm, name='norm_create'),
    path('positions/', views.position_list, name='position_list'),
    path('position/<int:position_id>/', views.position_detail, name='position_detail'),
]
