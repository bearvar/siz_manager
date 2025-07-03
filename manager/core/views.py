# Standard library imports
import json
import logging
import re
from collections import defaultdict
from datetime import date, datetime, timedelta
from io import BytesIO
from xmlrpc.client import Boolean

# Third-party imports
import openpyxl
import pandas as pd
from dateutil import parser
from dateutil.relativedelta import relativedelta

# Django imports
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import management
from django.core.paginator import Paginator
from django.db import models, transaction
from django.db.models import Q, Sum
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.core.management import call_command
from django.contrib import messages
from django.template.defaulttags import register
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_http_methods

# Local application imports
from .forms import (
    EmployeeForm, EmployeeImportItemsForm, FlushingAgentIssueForm,
    FlushingNormCreateForm, IssueCreateForm, NormCreateForm,
    NormHeightCreateForm, PositionForm, SAPImportForm
)
from .models import (
    Employee, FlushingAgentIssue, FlushingAgentNorm, FlushingAgentType,
    HeightGroup, Issue, Norm, NormHeight, PPEType, Position
)
from users.models import CustomUser

logger = logging.getLogger(__name__)


def health_check(request):
    """Simple health check endpoint returning JSON response"""
    return JsonResponse({"status": "ok"})

@login_required
def index(request):
    today = date.today()
    # Calculate current quarter and year
    current_quarter = (today.month - 1) // 3 + 1
    current_year = today.year
    
    # Calculate next quarter
    if current_quarter == 4:
        next_quarter = 1
        next_year = current_year + 1
    else:
        next_quarter = current_quarter + 1
        next_year = current_year
    
    quarters = []
    current_date = today
    for _ in range(4):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        
        # Determine quarter start and end dates
        if quarter == 1:
            start_date = date(year, 1, 1)
            end_date = date(year, 3, 31)
        elif quarter == 2:
            start_date = date(year, 4, 1)
            end_date = date(year, 6, 30)
        elif quarter == 3:
            start_date = date(year, 7, 1)
            end_date = date(year, 9, 30)
        else:
            start_date = date(year, 10, 1)
            end_date = date(year, 12, 31)
        
        quarters.append({
            'quarter': quarter,
            'year': year,
            'start_date': start_date,
            'end_date': end_date
        })
        
        current_date = end_date + relativedelta(days=1)
    
    quarterly_data = []
    # Prefetch all norms outside the loop
    all_positions = Position.objects.in_bulk()
    all_height_groups = HeightGroup.objects.in_bulk()
    
    # Collect all position and height group IDs
    position_ids = set()
    height_group_ids = set()
    
    for q in quarters:
        # Fetch active issues for the quarter
        issues = Issue.objects.filter(
            expiration_date__gte=q['start_date'],
            expiration_date__lte=q['end_date'],
            is_active=True
        ).select_related('employee', 'ppe_type').order_by('expiration_date')
        
        # Collect IDs for optimization
        for issue in issues:
            if issue.employee.position_id:
                position_ids.add(issue.employee.position_id)
            if issue.employee.height_group_id:
                height_group_ids.add(issue.employee.height_group_id)
    
    # Fetch all relevant norms
    position_norms = Norm.objects.filter(
        position_id__in=position_ids
    ).select_related('ppe_type')
    
    height_norms = NormHeight.objects.filter(
        height_group_id__in=height_group_ids
    ).select_related('ppe_type')
    
    # Group norms by position and height group
    norms_by_position = defaultdict(list)
    for norm in position_norms:
        norms_by_position[norm.position_id].append(norm)
    
    norms_by_height_group = defaultdict(list)
    for norm in height_norms:
        norms_by_height_group[norm.height_group_id].append(norm)
    
    for idx, q in enumerate(quarters):
        # Fetch active issues for the quarter
        issues = Issue.objects.filter(
            expiration_date__gte=q['start_date'],
            expiration_date__lte=q['end_date'],
            is_active=True
        ).select_related('employee', 'ppe_type').order_by('expiration_date')
        
        # Group by employee and aggregate issues
        employees_issues = defaultdict(list)
        for issue in issues:
            employees_issues[issue.employee].append(issue)
        
        employees_list = []
        for employee, items in employees_issues.items():
            # Group duplicate issues
            grouped = defaultdict(list)
            for issue in items:
                key = (issue.ppe_type_id, issue.item_name, issue.item_size, issue.issue_date, issue.expiration_date)
                grouped[key].append(issue)
            
            issue_groups = [
                {'issue': group[0], 'quantity': len(group)}
                for key, group in grouped.items()
            ]
            issue_groups = sorted(issue_groups, key=lambda x: x['issue'].expiration_date)
            
            # Add virtual items for missing PPE only in the next quarter
            if q['quarter'] == next_quarter and q['year'] == next_year:
                if employee.position_id or employee.height_group_id:
                    # Get all relevant norms
                    norms = []
                    
                    if employee.position_id:
                        norms.extend(norms_by_position.get(employee.position_id, []))
                    
                    if employee.height_group_id:
                        norms.extend(norms_by_height_group.get(employee.height_group_id, []))
                    
                    # Create set of issued PPE types
                    issued_ppe_types = {group['issue'].ppe_type_id for group in issue_groups}
                    
                    for norm in norms:
                        if norm.ppe_type_id not in issued_ppe_types:
                            # Create virtual issue for missing PPE
                            virtual_issue = type('obj', (object,), {
                                'ppe_type': norm.ppe_type,
                                'item_name': norm.ppe_type.name,
                                'item_size': None,
                                'expiration_date': q['start_date'],  # First day of quarter
                                'is_virtual': True
                            })
                            issue_groups.append({
                                'issue': virtual_issue,
                                'quantity': norm.quantity
                            })
            
            employees_list.append({
                'employee': employee,
                'issue_groups': issue_groups,
                'count': len(items),
                'flushing_needs': []  # Initialize empty list for flushing needs
            })
        
        # Add employee data to quarterly_data
        quarterly_data.append({
            'quarter': q['quarter'],
            'year': q['year'],
            'start_date': q['start_date'],
            'end_date': q['end_date'],
            'employees': employees_list,
            'total': issues.count()
        })
    
    # Calculate flushing agent needs for each employee in each quarter
    for quarter in quarterly_data:
        year = quarter['year']
        quarter_num = quarter['quarter']
        
        for emp_data in quarter['employees']:
            employee = emp_data['employee']
            if not employee.position:
                continue
            
            # Get flushing norms for the position
            flushing_norms = FlushingAgentNorm.objects.filter(position=employee.position)
            current_date = today.replace(day=1)
            flushing_needs = []
            
            for norm in flushing_norms:
                # Calculate current stock for the agent
                current_stock = FlushingAgentIssue.objects.filter(
                    employee=employee,
                    agent_type=norm.agent_type,
                    is_active=True
                ).aggregate(Sum('volume_ml'))['volume_ml__sum'] or 0
                
                # Get quarterly needs for this norm
                needs = norm.get_quarterly_needs(current_stock, current_date)
                for need in needs:
                    need_q_date = need['quarter']
                    need_year = need_q_date.year
                    need_quarter = (need_q_date.month - 1) // 3 + 1
                    
                    # Match current quarter in the loop
                    if need_year == year and need_quarter == quarter_num:
                        flushing_needs.append({
                            'agent_type': norm.agent_type,
                            'volume_ml': need['needed']
                        })
            
            # Attach flushing needs to the employee data
            emp_data['flushing_needs'] = flushing_needs
    
    context = {
        'title': 'Главная страница',
        'quarters': quarterly_data,
        'current_date': today
    }
    return render(request, 'core/index.html', context)


@login_required
def position_list(request):
    positions = Position.objects.all()
    return render(request, 'core/position_list.html', {'positions': positions})


@login_required
def profile(request, username):
    author_obj = get_object_or_404(CustomUser, username=username)
    # items = author_obj.items.all()
    # paginator = Paginator(items, 30)
    # page_number = request.GET.get('page')
    # page_obj = paginator.get_page(page_number)
    context = {
        'author_obj': author_obj,
        # 'items': items,
        # 'page_obj': page_obj,
    }
    return render(request, 'core/profile.html', context)


@login_required
def employee_create(request):
    if request.method == 'POST':
        form = EmployeeForm(request.POST)
        if form.is_valid():
            employee = form.save(commit=False)
            # Дополнительные проверки для высотной группы
            if employee.height_group and not employee.position:
                form.add_error('height_group', 
                    "Для назначения группы высоты требуется указать должность")
                return render(request, 'core/create_employee.html', {'form': form})
            employee.save()
            return redirect('core:employee_detail', employee_id=employee.id)
    else:
        form = EmployeeForm()
    return render(request, 'core/create_employee.html', {'form': form})


@login_required
def position_create(request):
    if request.method == 'POST':
        form = PositionForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('core:position_list')
    else:
        form = PositionForm()
    return render(request, 'core/create_position.html', {'form': form})


@login_required
@require_http_methods(["POST"])
def position_delete(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    
    if position.employees.exists():
        messages.error(request, 
            "Невозможно удалить должность, так как есть сотрудники с этой должностью")
    else:
        position.delete()
        messages.success(request, "Должность успешно удалена")
    
    return redirect('core:position_list')


@login_required
def create_norm(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    
    if request.method == 'POST':
        form = NormCreateForm(request.POST, position=position)
        if form.is_valid():
            form.save()
            return redirect('core:position_detail', position_id=position.id)
    else:
        form = NormCreateForm(position=position)
    
    return render(request, 'core/create_norm.html', {
        'form': form,
        'position': position
    })

@login_required
def create_flushing_norm(request, position_id):
    """Создание нормы для смывающих средств"""
    position = get_object_or_404(Position, pk=position_id)
    
    if request.method == 'POST':
        form = FlushingNormCreateForm(request.POST)
        if form.is_valid():
            norm = form.save(commit=False)
            norm.position = position
            norm.save()
            messages.success(request, 'Норма для смывающих средств успешно создана')
            return redirect('core:position_detail', position_id=position.id)
    else:
        form = FlushingNormCreateForm()
    
    return render(request, 'core/create_flushing_norm.html', {
        'form': form,
        'position': position
    })


@login_required
def position_detail(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    norms = Norm.objects.filter(position=position)
    flushing_norms = FlushingAgentNorm.objects.filter(position=position)
    return render(request, 'core/position_detail.html', {
        'position': position,
        'norms': norms,
        'flushing_norms': flushing_norms
    })


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    all_issues = Issue.objects.filter(employee=employee).order_by('expiration_date')
    norms_status = []
    today = date.today()
    
    # Group duplicate issues
    grouped_issues = defaultdict(list)
    for issue in all_issues:
        key = (
            issue.ppe_type_id,
            issue.item_name,
            issue.item_size,
            issue.issue_date,
            issue.expiration_date
        )
        grouped_issues[key].append(issue)
    
    # Create groups with quantity and sort by expiration date
    issue_groups = [
        {'issue': group[0], 'quantity': len(group)}
        for key, group in grouped_issues.items()
    ]
    issue_groups.sort(key=lambda x: x['issue'].expiration_date)
    
    # Собираем все применимые нормы
    norms = []
    if employee.position:
        norms += list(Norm.objects.filter(position=employee.position))
    if employee.height_group:
        norms += list(NormHeight.objects.filter(height_group=employee.height_group))
    
    # Группируем нормы по типу СИЗ
    ppe_norms = defaultdict(lambda: {
        'required': 0,
        'lifespan': 0,
        'ppe_type_obj': None
    })
    
    for norm in norms:
        ppe_type = norm.ppe_type
        ppe_norms[ppe_type]['required'] += norm.quantity
        ppe_norms[ppe_type]['ppe_type_obj'] = ppe_type
        # Берем максимальный срок из всех норм для этого СИЗ
        if hasattr(norm, 'lifespan'):
            lifespan = norm.lifespan
        else:
            lifespan = norm.lifespan  # Для NormHeight
        ppe_norms[ppe_type]['lifespan'] = max(
            ppe_norms[ppe_type]['lifespan'],
            lifespan
        )
    
    # Обрабатываем каждый тип СИЗ
    for ppe_type, norm_data in ppe_norms.items():
        ppe_issues = all_issues.filter(
            ppe_type=ppe_type,
            is_active=True
        )
        
        # Актуальные выдачи (не просроченные)
        valid_issues = ppe_issues.filter(
            Q(expiration_date__gte=today) | 
            Q(expiration_date__isnull=True)
        )
        valid_count = valid_issues.count()
        
        # Просроченные выдачи
        expired_issues = ppe_issues.filter(
            expiration_date__lt=today
        )
        
        # Статусные флаги
        status = []
        if expired_issues.exists():
            status.append("⛔ Просрочено")
        if valid_count < norm_data['required']:
            status.append(f"❗ Не хватает ({valid_count}/{norm_data['required']})")
        if valid_count > norm_data['required']:
            status.append(f"📦 Лишние ({valid_count - norm_data['required']} шт.)")
        
        # Источники норм
        sources = []
        if employee.position and Norm.objects.filter(position=employee.position, ppe_type=ppe_type).exists():
            sources.append("должность")
        if employee.height_group and NormHeight.objects.filter(height_group=employee.height_group, ppe_type=ppe_type).exists():
            sources.append("высота")
        
        norms_status.append({
            'ppe_type': ppe_type.name,
            'required': norm_data['required'],
            'actual': valid_count,
            'status': " | ".join(status) if status else "✅ В норме",
            'sources': ", ".join(sources)
        })
    
    # Сортируем по статусу и названию СИЗ
    norms_status.sort(key=lambda x: (x['status'] == "✅ В норме", x['ppe_type']))
    
    # Add flushing agent data
    flushing_issues = FlushingAgentIssue.objects.filter(employee=employee)
    
    context = {
        'employee': employee,
        'issue_groups': issue_groups,
        'norms_status': norms_status,
        'flushing_issues': flushing_issues,
    }
    return render(request, 'core/employee_detail.html', context)


@login_required
def norm_edit(request, position_id):
    position = get_object_or_404(
        Position.objects.prefetch_related('norms__ppe_type'), 
        pk=position_id
    )
    return render(request, 'core/norm_edit.html', {
        'position': position,
        'norms': position.norms.all()
    })

@login_required
@require_http_methods(["POST"])
def norm_update(request, norm_id):
    try:
        norm = Norm.objects.select_related('position').get(pk=norm_id)
        quantity = int(request.POST.get('quantity', 0))
        lifespan = int(request.POST.get('lifespan', 0))
        
        # Валидация данных
        if quantity < 1:
            raise ValueError("Количество должно быть положительным числом")
        if lifespan < 1:
            raise ValueError("Срок годности должен быть положительным числом")
            
        # Обновление данных
        norm.quantity = quantity
        norm.lifespan = lifespan
        norm.save()
        
        messages.success(request, f"Норма для {norm.ppe_type.name} обновлена")
        
    except Norm.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Ошибка при обновлении: {str(e)}")
    
    return redirect('core:norm_edit', position_id=norm.position.id)

@login_required
@require_http_methods(["POST"])
def norm_delete(request, norm_id):
    try:
        norm = Norm.objects.select_related('position').get(pk=norm_id)
        position_id = norm.position.id
        ppe_type_name = norm.ppe_type.name
        norm.delete()
        messages.success(request, f"Норма для {ppe_type_name} удалена")
    except Norm.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except Exception as e:
        messages.error(request, f"Ошибка при удалении: {str(e)}")
    
    return redirect('core:norm_edit', position_id=position_id)

@login_required
def flushing_norm_edit(request, position_id):
    position = get_object_or_404(
        Position.objects.prefetch_related('flushingnorms__agent_type'), 
        pk=position_id
    )
    return render(request, 'core/flushing_norm_edit.html', {
        'position': position,
        'norms': position.flushingnorms.all()
    })

@login_required
@require_http_methods(["POST"])
def flushing_norm_update(request, norm_id):
    try:
        norm = FlushingAgentNorm.objects.select_related('position').get(pk=norm_id)
        monthly_ml = int(request.POST.get('monthly_ml', 0))
        
        if monthly_ml < 1:
            raise ValueError("Месячная норма должна быть положительным числом")
            
        norm.monthly_ml = monthly_ml
        norm.save()
        
        messages.success(request, f"Норма для {norm.agent_type.name} обновлена")
        return redirect('core:flushing_norm_edit', position_id=norm.position.id)
        
    except FlushingAgentNorm.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Ошибка при обновлении: {str(e)}")
        logger.error(f"Flushing norm update error: {str(e)}")
    
    return redirect('core:flushing_norm_edit', position_id=norm.position.id)

@login_required
@require_http_methods(["POST"])
def flushing_norm_delete(request, norm_id):
    try:
        norm = FlushingAgentNorm.objects.select_related('position').get(pk=norm_id)
        position_id = norm.position.id
        agent_name = norm.agent_type.name
        norm.delete()
        messages.success(request, f"Норма для {agent_name} удалена")
    except FlushingAgentNorm.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except Exception as e:
        messages.error(request, f"Ошибка при удалении: {str(e)}")
        logger.error(f"Flushing norm delete error: {str(e)}")
    
    return redirect('core:flushing_norm_edit', position_id=position_id)


@login_required
def create_flushing_issue(request, employee_id):
    employee = get_object_or_404(Employee, id=employee_id)
    
    if not employee.position:
        messages.error(request, "Сотрудник не имеет назначенной должности")
        return redirect('core:employee_list')
    
    if request.method == 'POST':
        form = FlushingAgentIssueForm(request.POST, employee=employee)
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Manually parse date from form data
                    issue_date = form.cleaned_data['issue_date']
                    if isinstance(issue_date, str):
                        try:
                            issue_date = datetime.strptime(
                                issue_date, 
                                '%d.%m.%Y'
                            ).date()
                        except ValueError:
                            form.add_error('issue_date', 'Неверный формат даты. Используйте ДД.ММ.ГГГГ')
                            raise forms.ValidationError('Invalid date format')
                    
                    # Save through form with commit=False to set additional fields
                    issue = form.save(commit=False)
                    issue.employee = employee
                    issue.save()
                    
                    messages.success(request, 'Смывающее средство успешно выдано')
                    return redirect('core:employee_detail', employee_id=employee.id)
            except Exception as e:
                messages.error(request, f'Ошибка сохранения: {str(e)}')
        else:
            messages.error(request, 'Исправьте ошибки в форме')
    else:
        form = FlushingAgentIssueForm(
            employee=employee,
            initial={'issue_date': timezone.now().date()}
        )
    
    return render(request, 'core/create_flushing_issue.html', {
        'employee': employee,
        'form': form
    })

def create_issue(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if not employee.position:
        messages.error(request, "Сотрудник не имеет назначенной должности")
        return redirect('core:employee_list')
    
    if request.method == 'POST':
        form = IssueCreateForm(request.POST, employee=employee)
        if form.is_valid():
            # Получаем очищенные данные
            data = form.cleaned_data
            ppe_type = data['ppe_type']
            quantity = data['quantity']
            
            # Создаем записи
            for _ in range(quantity):
                Issue.objects.create(
                    employee=employee,
                    ppe_type=ppe_type,
                    item_name=data['item_name'],
                    issue_date=data['issue_date'],
                    item_size=data['item_size'],
                    item_mu=ppe_type.default_mu
                )
            
            messages.success(request, f"Успешно создано {quantity} выдач СИЗ")
            return redirect('core:employee_detail', employee_id=employee.id)
    else:
        form = IssueCreateForm(employee=employee)
    
    return render(request, 'core/create_issue.html', {
        'form': form,
        'employee': employee
    })


@login_required
def issue_edit(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    issues = Issue.objects.filter(employee=employee).select_related('ppe_type')
    all_employees = Employee.objects.all().order_by('last_name', 'first_name')
    return render(request, 'core/edit_issues.html', {
        'employee': employee,
        'issues': issues,
        'all_employees': all_employees,
    })

@login_required
def edit_flushing_issues(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    issues = FlushingAgentIssue.objects.filter(employee=employee).order_by('-issue_date')
    all_employees = Employee.objects.exclude(id=employee.id).order_by('last_name', 'first_name')
    return render(request, 'core/edit_flushing_issues.html', {
        'employee': employee,
        'flushing_issues': issues,
        'all_employees': all_employees
    })


@login_required
@require_http_methods(["POST"])
def issue_update(request, issue_id):
    issue = get_object_or_404(Issue.objects.select_related('employee'), pk=issue_id)
    employee_id = issue.employee.id
    
    try:
        original_issue_date = issue.issue_date
        original_expiration_date = issue.expiration_date
        
        issue.item_name = request.POST.get('item_name', '').strip()
        issue.item_size = request.POST.get('item_size', '').strip() or None
        
        # Парсинг даты в формате дд.мм.гггг
        issue.issue_date = datetime.strptime(
            request.POST['issue_date'].strip(),
            '%d.%m.%Y'
        ).date()
        
        expiration_date_str = request.POST.get('expiration_date', '').strip()
        if expiration_date_str:
            issue.expiration_date = datetime.strptime(
                expiration_date_str,
                '%d.%m.%Y'
            ).date()
        else:
            issue.expiration_date = None
        
        if issue.expiration_date != original_expiration_date:
            issue.save(update_fields=[
                'item_name', 
                'item_size', 
                'issue_date', 
                'expiration_date'
            ])
        else:
            issue.save()
        
        messages.success(request, "Изменения успешно сохранены")
    except ValueError as e:
        logger.error(f"Date parsing error: {str(e)}")
        messages.error(request, "Ошибка формата даты. Используйте формат дд.мм.гггг")
    except Exception as e:
        logger.error(f"Error updating issue {issue_id}: {str(e)}")
        messages.error(request, f"Ошибка сохранения: {str(e)}")
    
    return redirect('core:edit_issues', employee_id=employee_id)


@login_required
@require_http_methods(["POST"])
def issue_delete(request, issue_id):
    issue = get_object_or_404(Issue.objects.select_related('employee'), pk=issue_id)
    employee_id = issue.employee.id
    try:
        issue.delete()
        messages.success(request, "Выдача успешно удалена")
    except Exception as e:
        logger.error(f"Error deleting issue: {e}")
        messages.error(request, f"Ошибка удаления: {str(e)}")
    
    return redirect('core:edit_issues', employee_id=employee_id)


@login_required
@require_http_methods(["POST"])
def issue_transfer(request, issue_id):
    issue = get_object_or_404(Issue.objects.select_related('employee'), pk=issue_id)
    old_employee_id = issue.employee.id
    
    try:
        new_employee_id = request.POST.get('new_employee_id')
        if not new_employee_id:
            raise ValueError("Не выбран сотрудник для передачи")
        
        new_employee = get_object_or_404(Employee, pk=new_employee_id)
        
        # Проверяем, есть ли у нового сотрудника соответствующая норма
        norm_exists = False
        
        # Проверка норм по должности
        if new_employee.position:
            norm_exists = Norm.objects.filter(
                position=new_employee.position,
                ppe_type=issue.ppe_type
            ).exists()
        
        # Проверка норм по высотной группе
        if not norm_exists and new_employee.height_group:
            norm_exists = NormHeight.objects.filter(
                height_group=new_employee.height_group,
                ppe_type=issue.ppe_type
            ).exists()
        
        if not norm_exists:
            messages.error(request, f"У сотрудника {new_employee} нет соответствующей нормы для {issue.ppe_type.name}")
            return redirect('core:edit_issues', employee_id=old_employee_id)
        
        # Создаем копию записи для нового сотрудника
        Issue.objects.create(
            employee=new_employee,
            ppe_type=issue.ppe_type,
            item_name=issue.item_name,
            item_size=issue.item_size,
            issue_date=issue.issue_date,
            expiration_date=issue.expiration_date,
            is_active=True
        )
        
        # Удаляем исходную запись
        issue.delete()
        
        messages.success(request, f"СИЗ успешно передан сотруднику {new_employee}")
    except Exception as e:
        logger.error(f"Error transferring issue: {e}")
        messages.error(request, f"Ошибка передачи: {str(e)}")
    
    return redirect('core:edit_issues', employee_id=old_employee_id)


@login_required
@require_http_methods(["POST"])
def flushing_issue_transfer(request, issue_id):
    issue = get_object_or_404(FlushingAgentIssue.objects.select_related('employee'), pk=issue_id)
    old_employee_id = issue.employee.id
    logger.info(f"issue object: {issue}")
    
    try:
        new_employee_id = request.POST.get('new_employee_id')
        if not new_employee_id:
            raise ValueError("Не выбран сотрудник для передачи")
        
        new_employee = get_object_or_404(Employee, pk=new_employee_id)
        
        # Проверяем, есть ли у нового сотрудника соответствующая норма
        norm_exists = False
        
        # Проверка норм по должности
        if new_employee.position:
            norm_exists = FlushingAgentNorm.objects.filter(
                position=new_employee.position,
                agent_type=issue.agent_type
            ).exists()
        
        if not norm_exists:
            messages.error(request, f"У сотрудника {new_employee} нет соответствующей нормы для {issue.agent_type.name}")
            return redirect('core:edit_issues', employee_id=old_employee_id)
        
        # Создаем копию записи для нового сотрудника
        FlushingAgentIssue.objects.create(
            employee=new_employee,
            agent_type=issue.agent_type,
            item_name=issue.item_name,
            volume_ml_nominal=issue.volume_ml_nominal,
            volume_ml=issue.volume_ml,
            issue_date=issue.issue_date,
            is_active=True
        )
        
        # Удаляем исходную запись
        issue.delete()
        
        messages.success(request, f"Смывающее средство успешно передан сотруднику {new_employee}")
    except Exception as e:
        logger.error(f"Error transferring issue: {e}")
        messages.error(request, f"Ошибка передачи: {str(e)}")
    
    return redirect('core:edit_issues', employee_id=old_employee_id)


def employee_import_items(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    results = {'created': [], 'errors': []}
    issues_to_create = []  # List to collect valid Issue objects

    if request.method == 'POST':
        form = EmployeeImportItemsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = request.FILES['sap_file']
                df = pd.read_excel(BytesIO(file.read()))

                required_columns = [
                    'Наименование группы СИЗ',
                    'Наименование ОС',
                    'Базисная ЕИ',
                    'Прог.ДатаСписан',
                    'Срок использования',
                    'Получено.Количество'
                ]
                
                if not set(required_columns).issubset(df.columns):
                    missing = set(required_columns) - set(df.columns)
                    raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

                # Process each row and collect valid issues
                for index, row in df.iterrows():
                    try:
                        quantity = int(row['Получено.Количество'])
                        if quantity <= 0:
                            continue

                        ppe_name = str(row['Наименование группы СИЗ']).strip()
                        if not ppe_name:
                            raise ValueError("Пустое название типа СИЗ")
                        
                        ppe_type = PPEType.objects.get(name__iexact=ppe_name)
                        
                        norm_exists = False
                        if employee.position:
                            norm_exists = Norm.objects.filter(
                                position=employee.position,
                                ppe_type=ppe_type
                            ).exists()
                        
                        if not norm_exists and employee.height_group:
                            norm_exists = NormHeight.objects.filter(
                                height_group=employee.height_group,
                                ppe_type=ppe_type
                            ).exists()
                        
                        if not norm_exists:
                            raise ValueError(f"Нет нормы для типа СИЗ: {ppe_name}")
                        
                        excel_unit = str(row['Базисная ЕИ']).strip().lower()
                        model_unit = UNIT_CONVERSION.get(excel_unit)
                        if not model_unit:
                            raise ValueError(f"Недопустимая единица измерения: {excel_unit}")

                        expiration_date = None
                        if pd.notna(row['Прог.ДатаСписан']):
                            try:
                                expiration_date = parser.parse(str(row['Прог.ДатаСписан'])).date()
                            except:
                                raise ValueError("Неверный формат даты списания")

                        lifespan_months = int(row['Срок использования'])
                        issue_date = expiration_date - relativedelta(months=lifespan_months) if expiration_date else date.today()

                        item_name = str(row['Наименование ОС'])
                        item_size = "Не указан"
                        
                        size_patterns = [
                            r'(\d{2}-\d{2}\s*/\s*\d{3}-\d{3})\b',
                            r'\b(?:разм|р|размер)[.:]?\s*(\S+)',
                            r'\b(\d{2,3}(?:-\d{2,3})?)\b'
                        ]

                        for pattern in size_patterns:
                            match = re.search(pattern, item_name, re.IGNORECASE)
                            if match:
                                item_size = match.group(1)
                                item_name = re.sub(pattern, '', item_name, flags=re.IGNORECASE).strip()
                                break

                        # Create Issue objects and collect them
                        for _ in range(quantity):
                            issue = Issue(
                                employee=employee,
                                ppe_type=ppe_type,
                                item_name=item_name,
                                item_mu=model_unit,
                                issue_date=issue_date,
                                expiration_date=expiration_date,
                                item_size=item_size
                            )
                            issues_to_create.append(issue)
                        
                        results['created'].append({
                            'ppe_type': ppe_type.name,
                            'item_name': item_name,
                            'item_size': item_size,
                            'quantity': quantity,
                            'expiration_date': expiration_date
                        })

                    except ValueError as e:
                        results['errors'].append({
                            'type': 'row',
                            'row': index + 2,
                            'message': str(e),
                            'data': row.to_dict()
                        })
                    except PPEType.DoesNotExist:
                        results['errors'].append({
                            'type': 'row',
                            'row': index + 2,
                            'message': f"Тип СИЗ '{ppe_name}' не найден",
                            'data': row.to_dict()
                        })

                # Bulk create all valid issues
                if issues_to_create:
                    try:
                        with transaction.atomic():
                            Issue.objects.bulk_create(issues_to_create)
                    except Exception as e:
                        results['errors'].append({
                            'type': 'global',
                            'message': f"Ошибка при создании записей: {str(e)}"
                        })

            except Exception as e:
                results['errors'].append({
                    'type': 'global',
                    'message': str(e)
                })

            return render(request, 'core/import_item_results.html', {
                'employee': employee,
                'results': results
            })

    else:
        form = EmployeeImportItemsForm()

    return render(request, 'core/employee_import_items.html', {
        'employee': employee,
        'form': form
    })


@login_required
def edit_employee(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    
    if request.method == 'POST':
        try:
            # Обновляем основные поля
            employee.first_name = request.POST['first_name']
            employee.last_name = request.POST['last_name']
            employee.patronymic = request.POST.get('patronymic', '')
            employee.department = request.POST.get('department', '')
            
            # Обработка должности
            position_id = request.POST.get('position')
            if position_id:
                employee.position = Position.objects.get(pk=position_id)
            else:
                employee.position = None
                
            # Обработка группы высоты
            height_group_id = request.POST.get('height_group')
            if height_group_id:
                employee.height_group = HeightGroup.objects.get(pk=height_group_id)
            else:
                employee.height_group = None

            # Обработка размеров
            employee.body_size = request.POST.get('body_size')
            employee.head_size = request.POST.get('head_size')
            employee.glove_size = request.POST.get('glove_size')
            shoe_size = request.POST.get('shoe_size')
            employee.shoe_size = int(shoe_size) if shoe_size else None
            
            # Валидация
            if employee.height_group and not employee.position:
                raise ValidationError("Для назначения группы высоты требуется должность")
            
            employee.save()
            messages.success(request, "Данные сотрудника обновлены")
            return redirect('core:employee_detail', employee_id=employee.id)
            
        except Exception as e:
            logger.error(f"Error updating employee: {str(e)}")
            messages.error(request, f"Ошибка обновления: {str(e)}")
    
    # Контекст для GET-запроса
    context = {
        'employee': employee,
        'positions': Position.objects.all(),
        'height_groups': HeightGroup.objects.all().order_by('level'),
        'body_size_choices': Employee.BODY_SIZE_CHOICES,
        'head_size_choices': Employee.HEAD_SIZE_CHOICES,
        'glove_size_choices': Employee.GLOVE_SIZE_CHOICES,
        'shoe_size_choices': Employee.SHOE_SIZE_CHOICES,
    }
    return render(request, 'core/edit_employee.html', context)


def quarterly_ppe_needs(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    quarters = []
    current_date = today

    # Генерируем ближайшие 4 квартала
    for _ in range(4):
        current_quarter = (current_date.month - 1) // 3 + 1
        year = current_date.year
        if current_quarter == 1:
            end_date = date(year, 3, 31)
        elif current_quarter == 2:
            end_date = date(year, 6, 30)
        elif current_quarter == 3:
            end_date = date(year, 9, 30)
        else:
            end_date = date(year, 12, 31)
        quarters.append({
            'quarter': current_quarter,
            'year': year,
            'end_date': end_date
        })
        current_date = end_date + relativedelta(days=1)

    if not employee.position:
        return render(request, 'core/quarterly_issues.html', {
            'employee': employee,
            'error': 'Должность не назначена. Невозможно определить нормы.'
        })

    norms = Norm.objects.filter(position=employee.position).select_related('ppe_type')
    quarterly_data = []

    for q in quarters:
        quarter_info = {
            'quarter': q['quarter'],
            'year': q['year'],
            'end_date': q['end_date'],
            'needs': []
        }
        for norm in norms:
            active_issues = Issue.objects.filter(
                employee=employee,
                ppe_type=norm.ppe_type,
                is_active=True
            ).filter(
                Q(expiration_date__gte=q['end_date']) | Q(expiration_date__isnull=True)
            ).count()
            needed = max(norm.quantity - active_issues, 0)
            quarter_info['needs'].append({
                'ppe_type': norm.ppe_type.name,
                'required': norm.quantity,
                'active': active_issues,
                'needed': needed
            })
        quarterly_data.append(quarter_info)

    context = {
        'employee': employee,
        'quarters': quarterly_data
    }
    return render(request, 'core/quarterly_issues.html', context)

from django.db.models import Sum

def expiring_ppe_issues(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    quarters = []
    
    # Generate 4 upcoming quarters
    current_date = today
    for _ in range(4):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        
        # Determine quarter start and end dates
        if quarter == 1:
            start_date = date(year, 1, 1)
            end_date = date(year, 3, 31)
        elif quarter == 2:
            start_date = date(year, 4, 1)
            end_date = date(year, 6, 30)
        elif quarter == 3:
            start_date = date(year, 7, 1)
            end_date = date(year, 9, 30)
        else:
            start_date = date(year, 10, 1)
            end_date = date(year, 12, 31)
        
        quarters.append({
            'quarter': quarter,
            'year': year,
            'start_date': start_date,
            'end_date': end_date
        })
        
        # Move to next quarter
        current_date = end_date + relativedelta(days=1)

    # Initialize quarterly_issues
    quarterly_issues = []
    
    # Collect quarterly data
    for q in quarters:
        # Fetch issues for the quarter
        issues = Issue.objects.filter(
            employee=employee,
            expiration_date__gte=q['start_date'],
            expiration_date__lte=q['end_date'],
            is_active=True
        ).select_related('ppe_type').order_by('expiration_date')
        
        # Group duplicates
        grouped = defaultdict(list)
        for issue in issues:
            key = (
                issue.ppe_type_id,
                issue.item_name,
                issue.item_size,
                issue.issue_date,
                issue.expiration_date
            )
            grouped[key].append(issue)
        
        # Create issue groups with quantity
        issue_groups = [
            {'issue': group[0], 'quantity': len(group)}
            for key, group in grouped.items()
        ]
        # Sort by expiration date
        issue_groups = sorted(issue_groups, key=lambda x: x['issue'].expiration_date)
        
        quarterly_issues.append({
            'quarter': q['quarter'],
            'year': q['year'],
            'start_date': q['start_date'],
            'end_date': q['end_date'],
            'issue_groups': issue_groups,
            'count': issues.count()
        })
    
    # Calculate flushing agent needs if the employee has a position
    if employee.position:
        current_date = today.replace(day=1)
        flushing_norms = FlushingAgentNorm.objects.filter(position=employee.position)
        
        # Lookup dictionary for quarterly needs {(year, quarter): {agent: ml}}
        quarter_needs_lookup = defaultdict(lambda: defaultdict(int))
        
        for norm in flushing_norms:
            # Get current stock for the agent type
            current_stock = FlushingAgentIssue.objects.filter(
                employee=employee,
                agent_type=norm.agent_type,
                is_active=True
            ).aggregate(Sum('volume_ml'))['volume_ml__sum'] or 0
            
            # Calculate quarterly needs
            needs = norm.get_quarterly_needs(current_stock, current_date)
            for need in needs:
                q_date = need['quarter']
                quarter_key = (q_date.year, (q_date.month - 1) // 3 + 1)
                quarter_needs_lookup[quarter_key][norm.agent_type] += need['needed']
        
        # Attach flushing needs to each quarter in quarterly_issues
        for q in quarterly_issues:
            year_quarter = (q['year'], q['quarter'])
            needs = quarter_needs_lookup.get(year_quarter, {})
            q['flushing_needs'] = [
                {'agent_type': agent, 'volume_ml': ml}
                for agent, ml in needs.items() if ml > 0
            ]
    
    context = {
        'employee': employee,
        'quarterly_issues': quarterly_issues,
        'today': today
    }
    return render(request, 'core/expiring_issues.html', context)


@login_required
def height_group_list(request):
    groups = HeightGroup.objects.all().order_by('level')
    return render(request, 'core/height_group_list.html', {'groups': groups})


@login_required
def height_group_detail(request, group_id):
    group = get_object_or_404(HeightGroup, pk=group_id)
    norms = NormHeight.objects.filter(height_group=group)
    return render(request, 'core/height_group_detail.html', {'group': group, 'norms': norms})


@login_required
def create_norm_height(request, group_id):
    group = get_object_or_404(HeightGroup, pk=group_id)
    
    if request.method == 'POST':
        form = NormHeightCreateForm(request.POST, height_group=group)
        if form.is_valid():
            form.save()
            messages.success(request, "Норма успешно добавлена!")
            return redirect('core:height_group_detail', group_id=group.id)
        else:
            messages.error(request, "Исправьте ошибки в форме")
    else:
        form = NormHeightCreateForm(height_group=group)
    
    return render(request, 'core/create_norm_height.html', {
        'form': form,
        'group': group
    })

@login_required
def norm_height_edit(request, group_id):
    group = get_object_or_404(
        HeightGroup.objects.prefetch_related('norms__ppe_type'), 
        pk=group_id
    )
    return render(request, 'core/norm_height_edit.html', {
        'group': group,
        'norms': group.norms.all()
    })


@login_required
@require_http_methods(["POST"])
def norm_height_update(request, norm_id):
    try:
        norm = NormHeight.objects.select_related('height_group').get(pk=norm_id)
        lifespan = int(request.POST.get('lifespan', 0))
        
        # Валидация данных
        if lifespan < 1:
            raise ValueError("Срок годности должен быть положительным числом")
            
        # Обновление данных
        norm.lifespan = lifespan
        norm.save()
        
        messages.success(request, f"Норма для {norm.ppe_type.name} обновлена")
        
    except NormHeight.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except ValueError as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Ошибка при обновлении: {str(e)}")
    
    return redirect('core:norm_height_edit', group_id=norm.height_group.id)

@login_required
@require_http_methods(["POST"])
def norm_height_delete(request, norm_id):
    try:
        norm = NormHeight.objects.select_related('height_group').get(pk=norm_id)
        group_id = norm.height_group.id
        ppe_type_name = norm.ppe_type.name
        norm.delete()
        messages.success(request, f"Норма для {ppe_type_name} удалена")
    except NormHeight.DoesNotExist:
        messages.error(request, "Норма не найдена")
    except Exception as e:
        messages.error(request, f"Ошибка при удалении: {str(e)}")
    
    return redirect('core:norm_height_edit', group_id=group_id)


UNIT_CONVERSION = {
    "кмп": "компл.",
    "кмп.": "компл.",
    "шт": "шт.",
    "пар": "пар.",
    "г": "г.",
    "мл": "мл.",
    "компл": "компл.",
    "пары": "пар.",
    "штук": "шт.",
}

@login_required
def sap_import(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    results = {'created': [], 'errors': []}

    # Проверка на существующие нормы
    if Norm.objects.filter(position=position).exists():
        results['errors'].append({
            'type': 'global',
            'message': 'Импорт невозможен: для этой должности уже существуют нормы'
        })
        return render(request, 'core/import_results.html', {
            'position': position,
            'results': results
        })

    if request.method == 'POST':
        form = SAPImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    file = request.FILES['sap_file']
                    
                    # Чтение Excel файла
                    try:
                        df = pd.read_excel(BytesIO(file.read()))
                    except Exception as e:
                        raise ValueError(f"Ошибка чтения файла: {str(e)}")

                    # Проверка обязательных колонок
                    required_columns = [
                        'Наименование группы (краткое)',
                        'Единица измерения', 
                        'Лимит',
                        'Срок использования',
                        'К выдаче'
                    ]
                    
                    if not set(required_columns).issubset(df.columns):
                        missing = set(required_columns) - set(df.columns)
                        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

                    # Фильтрация по колонке "К выдаче"
                    try:
                        # Конвертируем все значения в строки и обрабатываем
                        df['К выдаче'] = df['К выдаче'].astype(str).str.strip().str.lower()
                        
                        # Заменяем булевы значения на строковые
                        df['К выдаче'] = df['К выдаче'].replace({
                            'true': 'true',
                            'false': 'false',
                            '1': 'true',
                            '0': 'false',
                            'да': 'true',
                            'нет': 'false'
                        })
                        
                        # Фильтруем только строки с true
                        df = df[df['К выдаче'] == 'true']
                    
                    except KeyError:
                        raise ValueError("Колонка 'К выдаче' не найдена в файле")
                    except Exception as e:
                        raise ValueError(f"Ошибка обработки колонки 'К выдаче': {str(e)}")
                    
                    if df.empty:
                        raise ValueError("Нет данных для импорта после фильтрации")

                    # Обработка строк
                    for index, row in df.iterrows():
                        try:
                            # Конвертация единиц измерения
                            excel_unit = str(row['Единица измерения']).strip().lower()
                            model_unit = UNIT_CONVERSION.get(excel_unit)

                            if not model_unit:
                                raise ValueError(
                                    f"Недопустимая единица измерения: {excel_unit}. "
                                    f"Допустимые значения: {', '.join(UNIT_CONVERSION.keys())}"
                                )
                            
                            # Создание/получение типа СИЗ
                            ppe_name = str(row['Наименование группы (краткое)']).strip()
                            if not ppe_name:
                                raise ValueError("Пустое значение в колонке 'Наименование группы (краткое)'")
                            
                            ppe_type, _ = PPEType.objects.get_or_create(
                                name=row['Наименование группы (краткое)'],
                                defaults={'default_mu': row['Единица измерения']}
                            )
                            
                            # Создание нормы
                            quantity = row['Лимит']
                            if quantity < 0:
                                raise ValueError("Лимит не может быть отрицательным")

                            lifespan = row['Срок использования']
                            if lifespan < 1:
                                raise ValueError("Срок использования должен быть не менее 1 месяца")
                            
                            Norm.objects.create(
                                position=position,
                                ppe_type=ppe_type,
                                quantity=int(row['Лимит']),
                                lifespan=int(row['Срок использования'])
                            )
                            
                            results['created'].append({
                                'ppe_type': ppe_type.name,
                                'quantity': row['Лимит'],
                                'lifespan': row['Срок использования']
                            })

                        except Exception as e:
                            results['errors'].append({
                                'type': 'row',
                                'row': index + 2,
                                'message': str(e),
                                'data': row.to_dict()
                            })

                    # Если все строки содержат ошибки
                    if len(results['errors']) == len(df):
                        raise ValueError("Все строки содержат ошибки, импорт отменен")

                    return render(request, 'core/import_results.html', {
                        'position': position,
                        'results': results
                    })

            except Exception as e:
                results['errors'].append({
                    'type': 'global', 
                    'message': str(e)
                })
                return render(request, 'core/import_results.html', {
                    'position': position,
                    'results': results
                })

    else:
        form = SAPImportForm()

    return render(request, 'core/sap_import.html', {
        'position': position,
        'form': form
    })

@login_required
@require_http_methods(["POST"])
def delete_employee(request, employee_id):
    logger.info(f"Delete employee request received for employee_id: {employee_id}")
    try:
        employee = get_object_or_404(Employee, id=employee_id)
        logger.info(f"Found employee: {employee}")
        # Delete all related issues first
        issues_count = employee.issues.all().delete()
        logger.info(f"Deleted {issues_count} issues")
        # Then delete the employee
        employee.delete()
        logger.info("Employee deleted successfully")
        messages.success(request, f'Сотрудник {employee} и все выданные ему СИЗ успешно удалены.')
        return redirect('core:employee_list')
    except Exception as e:
        logger.error(f"Error deleting employee: {str(e)}")
        messages.error(request, f'Ошибка при удалении сотрудника: {str(e)}')
        return redirect('core:employee_detail', employee_id=employee_id)


@login_required
@require_http_methods(["POST"])
def flushing_issue_update(request, issue_id):
    issue = get_object_or_404(FlushingAgentIssue, pk=issue_id)
    employee_id = issue.employee.id
    try:
        new_volume_ml_nominal = float(request.POST.get('volume_ml_nominal', 0))
        current_volume_ml = issue.volume_ml
        current_nominal = issue.volume_ml_nominal

        # Calculate new volume_ml based on current state
        if current_nominal == current_volume_ml:
            new_volume_ml = new_volume_ml_nominal
        else:
            new_volume_ml = (new_volume_ml_nominal - current_nominal) + current_volume_ml

        # Check if the new volume_ml is negative
        if new_volume_ml < 0:
            messages.error(request, "Объем (текущий) не может быть отрицательным")
            return redirect('core:edit_flushing_issues', employee_id=employee_id)

        # Update other fields
        issue.item_name = request.POST.get('item_name', '').strip()
        issue.volume_ml = new_volume_ml
        issue.volume_ml_nominal = new_volume_ml_nominal
        issue.issue_date = datetime.strptime(
            request.POST['issue_date'].strip(),
            '%d.%m.%Y'
        ).date()
        
        issue.save()
        management.call_command('process_flushing_agents')
        messages.success(request, "Изменения смывающего средства сохранены и обработка выполнена")
    except Exception as e:
        messages.error(request, f"Ошибка обновления: {str(e)}")
    return redirect('core:edit_flushing_issues', employee_id=employee_id)

@login_required
@require_http_methods(["POST"])
def flushing_issue_delete(request, issue_id):
    issue = get_object_or_404(FlushingAgentIssue, pk=issue_id)
    employee_id = issue.employee.id
    try:
        issue.delete()
        messages.success(request, "Смывающее средство удалено")
    except Exception as e:
        messages.error(request, f"Ошибка удаления: {str(e)}")
    return redirect('core:edit_flushing_issues', employee_id=employee_id)

@login_required
@require_http_methods(["POST"])
def process_flushing_agents(request):
    """Глобальный пересчет смывающих средств для всех сотрудников"""
    employee_id = request.POST.get('employee_id')
    if not employee_id:
        messages.error(request, 'Не указан ID сотрудника')
        return redirect('core:index')
    
    try:
        management.call_command('process_flushing_agents')
        messages.success(request, 'Пересчет смывающих средств для всех сотрудников выполнен')
    except Exception as e:
        logger.error(f"Ошибка обработки смывающих средств: {str(e)}", exc_info=True)
        messages.error(request, f'Ошибка при обработке: {str(e)}')
    return redirect('core:employee_detail', employee_id=employee_id)
