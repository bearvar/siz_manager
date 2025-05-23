from django.urls import path
from django.http import JsonResponse
from . import views

def health_check(request):
    return JsonResponse({"status": "ok"})

app_name = 'core'

urlpatterns = [
    path('health/', health_check, name='health_check'),
    path('', views.index, name='index'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('position/create/', views.position_create, name='position_create'),
    path('norm/create/<int:position_id>/', views.create_norm, name='norm_create'),
    path('flushing-norm/create/<int:position_id>/', views.create_flushing_norm, name='flushing_norm_create'),
    path('positions/', views.position_list, name='position_list'),
    path('position/<int:position_id>/', views.position_detail, name='position_detail'),
    path('position/<int:position_id>/import-sap/', views.sap_import, name='sap_import'),
    path('position/delete/<int:position_id>/', views.position_delete, name='position_delete'),
    path('employees/', views.employee_list, name='employee_list'),
    path('employees/<int:employee_id>/', views.employee_detail, name='employee_detail'),
    path('employees/<int:employee_id>/import-items/', views.employee_import_items, name='employee_import_items'),
    path('items/<int:employee_id>/', views.employee_detail, name='list_items'),
    path('norm/edit/<int:position_id>/', views.norm_edit, name='norm_edit'),
    path('norm/update/<int:norm_id>/', views.norm_update, name='norm_update'),
    path('norm/delete/<int:norm_id>/', views.norm_delete, name='norm_delete'),
    path('flushing-norm/edit/<int:position_id>/', views.flushing_norm_edit, name='flushing_norm_edit'),
    path('flushing-norm/update/<int:norm_id>/', views.flushing_norm_update, name='flushing_norm_update'),
    path('flushing-norm/delete/<int:norm_id>/', views.flushing_norm_delete, name='flushing_norm_delete'),
    path('employees/<int:employee_id>/issues/create/', views.create_issue, name='create_issue'),
    path('employees/<int:employee_id>/flush/create/', views.create_flushing_issue, name='create_flushing_issue'),
    path('employees/<int:employee_id>/flush/edit/', views.edit_flushing_issues, name='edit_flushing_issues'),
    path('flush/update/<int:issue_id>/', views.flushing_issue_update, name='flushing_issue_update'),
    path('flush/delete/<int:issue_id>/', views.flushing_issue_delete, name='flushing_issue_delete'),
    path('flush/transfer/<int:issue_id>/', views.flushing_issue_transfer, name='flushing_issue_transfer'),
    path('employees/<int:employee_id>/issues/edit/', views.issue_edit, name='edit_issues'),
    path('issue/update/<int:issue_id>/', views.issue_update, name='issue_update'),
    path('issue/delete/<int:issue_id>/', views.issue_delete, name='issue_delete'),
    path('issue/transfer/<int:issue_id>/', views.issue_transfer, name='issue_transfer'),
    path('employees/<int:employee_id>/edit/', views.edit_employee, name='edit_employee'),
    path('employees/<int:employee_id>/delete/', views.delete_employee, name='delete_employee'),
    path('employees/<int:employee_id>/quarterly_needs/', views.quarterly_ppe_needs, name='quarterly_needs'),
    path('employees/<int:employee_id>/expiring_issues/', views.expiring_ppe_issues, name='expiring_issues'),
    path('process-flushing-agents/', views.process_flushing_agents, name='process_flushing_agents'),
    
    path('height_groups/', views.height_group_list, name='height_group_list'),
    path('height_group/<int:group_id>/', views.height_group_detail, name='height_group_detail'),
    path('norm_height/create/<int:group_id>/', views.create_norm_height, name='norm_height_create'),
    path('norm_height/edit/<int:group_id>/', views.norm_height_edit, name='norm_height_edit'),
    path('norm_height/update/<int:norm_id>/', views.norm_height_update, name='norm_height_update'),
    path('norm_height/delete/<int:norm_id>/', views.norm_height_delete, name='norm_height_delete'),
]
