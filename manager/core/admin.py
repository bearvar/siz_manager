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

@admin.register(FlushingAgentType)
class FlushingAgentTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)

@admin.register(FlushingAgentNorm)
class FlushingAgentNormAdmin(admin.ModelAdmin):
    list_display = ('position', 'agent_type', 'monthly_ml')
    list_filter = ('position', 'agent_type')
    search_fields = ('position__position_name', 'agent_type__name')

@admin.register(FlushingAgentIssue)
class FlushingAgentIssueAdmin(admin.ModelAdmin):
    list_display = ('employee', 'agent_type', 'volume_ml', 'issue_date')
    list_filter = ('agent_type',)
    search_fields = ('employee__last_name', 'agent_type__name')
    date_hierarchy = 'issue_date'
