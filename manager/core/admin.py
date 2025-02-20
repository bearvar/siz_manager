from django.contrib import admin
from .models import Position, Employee, Item, Norm, Issue

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('position_name',)
    search_fields = ('position_name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'position', 'department')
    list_filter = ('position', 'department')
    search_fields = ('last_name', 'first_name', 'patronymic', 'department')

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ('item_name', 'item_size', 'item_mu')
    search_fields = ('item_name', 'item_size')
    list_filter = ('item_mu',)

@admin.register(Norm)
class NormAdmin(admin.ModelAdmin):
    list_display = ('position', 'item_type', 'quantity')
    list_filter = ('position', 'item_type')
    search_fields = ('item_type',)

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('employee', 'item_type', 'issue_date', 'expiration_date', 'is_active')
    list_filter = ('is_active', 'issue_date', 'expiration_date')
    search_fields = ('employee__last_name', 'employee__first_name', 'item_type')
