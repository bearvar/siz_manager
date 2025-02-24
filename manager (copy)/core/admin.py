from django.contrib import admin
from .models import Position, Employee, Norm, Issue

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('position_name',)
    search_fields = ('position_name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'position', 'department')
    list_filter = ('position', 'department')
    search_fields = ('last_name', 'first_name', 'patronymic', 'department')
