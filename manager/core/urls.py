from django.urls import path
from . import views

app_name = 'core'

urlpatterns = [
    path('', views.index, name='index'),
    # path('persons/', views.person_list, name='person_list'),
    # path('person/<int:tabel_number>/', views.person_items, name='person_items'),
    path('profile/<str:username>/', views.profile, name='profile'),
    path('employee/create/', views.employee_create, name='employee_create'),
    path('position/create/', views.position_create, name='position_create'),
    # path('items/<int:item_id>/', views.item_detail, name='item_detail'),
    # path('create/', views.item_create, name='item_create'),
    # path('items/<int:item_id>/edit', views.item_edit, name='item_edit'),
    # path('items/<int:item_id>/delete', views.item_delete, name='item_delete'),
    # path('inspect-ppe/', views.inspect_ppe, name='inspect_ppe'),
]
