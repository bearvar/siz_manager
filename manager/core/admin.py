from django.contrib import admin
from .models import (
    Position, Employee, Norm, Issue,
    FlushingAgentType, FlushingAgentNorm,
    FlushingAgentIssue
)

@admin.register(Position)
class PositionAdmin(admin.ModelAdmin):
    list_display = ('position_name',)
    search_fields = ('position_name',)

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('last_name', 'first_name', 'patronymic', 'position', 'department')
    list_filter = ('position', 'department')
    search_fields = ('last_name', 'first_name', 'patronymic', 'department')

@admin.register(Norm)
class NormAdmin(admin.ModelAdmin):
    list_display = ('position', 'ppe_type', 'quantity', 'lifespan')
    list_filter = ('position', 'ppe_type')
    search_fields = ('position__position_name', 'ppe_type__name')
    raw_id_fields = ('position', 'ppe_type')

@admin.register(Issue)
class IssueAdmin(admin.ModelAdmin):
    list_display = ('employee', 'ppe_type', 'item_name', 'issue_date', 'expiration_date', 'is_active')
    list_filter = ('ppe_type', 'is_active')
    search_fields = ('employee__last_name', 'item_name', 'ppe_type__name')
    raw_id_fields = ('employee', 'ppe_type')
    date_hierarchy = 'issue_date'
    list_editable = ('item_name',)
    verbose_name = 'Выдача'
    verbose_name_plural = 'Выдачи'

@admin.register(FlushingAgentType)
class FlushingAgentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(FlushingAgentNorm)
class FlushingAgentNormAdmin(admin.ModelAdmin):
    list_display = ('position', 'agent_type', 'monthly_ml', 'monthly_ml_per_employee')
    list_filter = ('position', 'agent_type')
    search_fields = ('position__position_name', 'agent_type__name')
    raw_id_fields = ('position', 'agent_type')

    def monthly_ml_per_employee(self, obj):
        return f"{obj.monthly_ml / 30:.1f} ml/day"
    monthly_ml_per_employee.short_description = 'Daily per employee'

@admin.register(FlushingAgentIssue)
class FlushingAgentIssueAdmin(admin.ModelAdmin):
    list_display = ('employee', 'agent_type', 'volume_ml', 'issue_date', 'is_active')
    list_filter = ('agent_type', 'is_active')
    search_fields = ('employee__last_name', 'agent_type__name')
    date_hierarchy = 'issue_date'
    raw_id_fields = ('employee', 'agent_type')
    list_editable = ('volume_ml', 'is_active')
