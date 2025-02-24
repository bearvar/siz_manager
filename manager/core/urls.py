from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('items/<int:employee_id>/', views.list_items, name='list_items'),
    path('', views.index, name='index'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('position/create/', views.position_create, name='position_create'),
    path('norm/create/<int:position_id>/', views.create_norm, name='norm_create'),
    path('positions/', views.position_list, name='position_list'),
    path('position/<int:position_id>/', views.position_detail, name='position_detail'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('norm/edit/<int:position_id>/', views.norm_edit, name='norm_edit'),
    path('norm/update/<int:norm_id>/', views.norm_update, name='norm_update'),
    path('norm/delete/<int:norm_id>/', views.norm_delete, name='norm_delete'),
    path('employees/<int:employee_id>/issues/create/', views.create_issue, name='create_issue'),
    path('employees/<int:employee_id>/issues/edit/', views.issue_edit, name='edit_issues'),
    path('issue/update/<int:issue_id>/', views.issue_update, name='issue_update'),
    path('issue/delete/<int:issue_id>/', views.issue_delete, name='issue_delete'),
    path('employees/<int:employee_id>/edit/', views.edit_employee, name='edit_employee'),
]
