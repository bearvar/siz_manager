import json
import logging
import openpyxl
from collections import defaultdict
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from .forms import EmployeeForm, IssueCreateForm, NormCreateForm, PositionForm, NormHeightCreateForm, SAPImportForm, EmployeeImportItemsForm
from .models import Employee, Issue, Norm, PPEType, Position, NormHeight, HeightGroup
from users.models import CustomUser
from xmlrpc.client import Boolean
from django.views.decorators.http import require_http_methods
from django.template.defaulttags import register
from django.db import transaction
from django import forms
import pandas as pd
from io import BytesIO
from dateutil import parser


logger = logging.getLogger(__name__)


def index(request):
    today = date.today()
    quarters = []
    
    # Генерируем 4 ближайших квартала
    current_date = today
    for _ in range(4):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        
        # Определяем даты начала и конца квартала
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
        
        # Переходим к следующему кварталу
        current_date = end_date + relativedelta(days=1)
    
    # Собираем данные по каждому кварталу
    quarterly_data = []
    for q in quarters:
        # Получаем все активные выдачи для квартала
        issues = Issue.objects.filter(
            expiration_date__gte=q['start_date'],
            expiration_date__lte=q['end_date'],
            is_active=True
        ).select_related('employee', 'ppe_type').order_by('expiration_date')
        
        # Группируем по сотрудникам
        employees_issues = defaultdict(list)
        for issue in issues:
            employees_issues[issue.employee].append(issue)
        
        # Формируем структуру данных для шаблона
        employees_list = []
        for employee, items in employees_issues.items():
            employees_list.append({
                'employee': employee,
                'issues': items,
                'count': len(items)
            })
        
        quarterly_data.append({
            'quarter': q['quarter'],
            'year': q['year'],
            'start_date': q['start_date'],
            'end_date': q['end_date'],
            'employees': employees_list,
            'total': issues.count()
        })
    
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
            return redirect('core:index')  # Redirect to the index page after successful creation
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
def position_detail(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    norms = Norm.objects.filter(position=position)
    return render(request, 'core/position_detail.html', {'position': position, 'norms': norms})


@login_required
def employee_list(request):
    employees = Employee.objects.all()
    return render(request, 'core/employee_list.html', {'employees': employees})


def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    all_issues = Issue.objects.filter(employee=employee).order_by('expiration_date')
    norms_status = []
    today = date.today()
    
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
    
    context = {
        'employee': employee,
        'issues': all_issues,
        'norms_status': norms_status
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
    return render(request, 'core/edit_issues.html', {
        'employee': employee,
        'issues': issues,
    })


@login_required
@require_http_methods(["POST"])
def issue_update(request, issue_id):
    issue = get_object_or_404(Issue.objects.select_related('employee'), pk=issue_id)
    employee_id = issue.employee.id
    
    try:
        # Сохраняем исходные значения перед изменениями
        original_issue_date = issue.issue_date
        original_expiration_date = issue.expiration_date
        
        # Обновляем поля
        issue.item_name = request.POST.get('item_name', '').strip()
        issue.item_size = request.POST.get('item_size', '').strip() or None
        issue.issue_date = datetime.strptime(
            request.POST['issue_date'], 
            '%Y-%m-%d'
        ).date()
        
        # Обрабатываем дату списания
        expiration_date_str = request.POST.get('expiration_date')
        if expiration_date_str:
            issue.expiration_date = datetime.strptime(
                expiration_date_str, 
                '%Y-%m-%d'
            ).date()
        else:
            issue.expiration_date = None
        
        # Сохраняем только если дата списания была изменена вручную
        if issue.expiration_date != original_expiration_date:
            issue.save(update_fields=[
                'item_name', 
                'item_size', 
                'issue_date', 
                'expiration_date'
            ])
        else:
            # Принудительно вызываем save() для пересчета срока
            issue.save()
        
        messages.success(request, "Изменения успешно сохранены")
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


def expiring_ppe_issues(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    today = date.today()
    quarters = []
    
    # Генерируем 4 ближайших квартала
    current_date = today
    for _ in range(4):
        year = current_date.year
        quarter = (current_date.month - 1) // 3 + 1
        
        # Определяем даты начала и конца квартала
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
        
        # Переходим к следующему кварталу
        current_date = end_date + relativedelta(days=1)
    
    # Собираем данные по каждому кварталу
    quarterly_issues = []
    for q in quarters:
        issues = Issue.objects.filter(
            employee=employee,
            expiration_date__gte=q['start_date'],
            expiration_date__lte=q['end_date'],
            is_active=True
        ).select_related('ppe_type').order_by('expiration_date')
        
        quarterly_issues.append({
            'quarter': q['quarter'],
            'year': q['year'],
            'issues': issues,
            'count': issues.count()
        })
    
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
def employee_import_items(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    results = {'created': [], 'errors': []}

    if request.method == 'POST':
        form = EmployeeImportItemsForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                with transaction.atomic():
                    file = request.FILES['sap_file']
                    
                    try:
                        df = pd.read_excel(BytesIO(file.read()))
                    except Exception as e:
                        raise ValueError(f"Ошибка чтения файла: {str(e)}")

                    required_columns = [
                        'Наименование группы СИЗ',
                        'Наименование ОС',
                        'Базисная ЕИ',
                        'Прог.ДатаСписан',
                        'Срок использования',
                        'Получено.Количество'  # Добавляем обязательную колонку
                    ]
                    
                    if not set(required_columns).issubset(df.columns):
                        missing = set(required_columns) - set(df.columns)
                        raise ValueError(f"Отсутствуют колонки: {', '.join(missing)}")

                    for index, row in df.iterrows():
                        try:
                            # Пропускаем строки с нулевым количеством
                            quantity = int(row['Получено.Количество'])
                            if quantity <= 0:
                                continue

                            # Проверка типа СИЗ
                            ppe_name = str(row['Наименование группы СИЗ']).strip()
                            if not ppe_name:
                                raise ValueError("Пустое название типа СИЗ")
                            
                            ppe_type = PPEType.objects.get(name__iexact=ppe_name)
                            
                            # Проверка существования нормы
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
                            
                            # Конвертация единиц измерения
                            excel_unit = str(row['Базисная ЕИ']).strip().lower()
                            model_unit = UNIT_CONVERSION.get(excel_unit)
                            if not model_unit:
                                raise ValueError(f"Недопустимая единица измерения: {excel_unit}")

                            # Обработка дат
                            expiration_date = None
                            if pd.notna(row['Прог.ДатаСписан']):
                                try:
                                    expiration_date = parser.parse(str(row['Прог.ДатаСписан'])).date()
                                except:
                                    raise ValueError("Неверный формат даты списания")

                            # Расчет даты выдачи
                            issue_date = None
                            if pd.notna(row['Срок использования']):
                                lifespan_months = int(row['Срок использования'])
                                if expiration_date:
                                    issue_date = expiration_date - relativedelta(months=lifespan_months)
                                else:
                                    issue_date = date.today()

                            # Создание нескольких выдач
                            for _ in range(quantity):
                                Issue.objects.create(
                                    employee=employee,
                                    ppe_type=ppe_type,
                                    item_name=row['Наименование ОС'],
                                    item_mu=model_unit,
                                    issue_date=issue_date,
                                    expiration_date=expiration_date,
                                    item_size=None
                                )
                            
                            results['created'].append({
                                'ppe_type': ppe_type.name,
                                'item_name': row['Наименование ОС'],
                                'quantity': quantity,
                                'expiration_date': expiration_date
                            })

                        except ValueError as e:
                            if 'Получено.Количество' in str(e):
                                results['errors'].append({
                                    'type': 'row',
                                    'row': index + 2,
                                    'message': f"Некорректное количество: {row['Получено.Количество']}",
                                    'data': row.to_dict()
                                })
                            else:
                                raise e
                        except PPEType.DoesNotExist:
                            results['errors'].append({
                                'type': 'row',
                                'row': index + 2,
                                'message': f"Тип СИЗ '{ppe_name}' не найден",
                                'data': row.to_dict()
                            })
                        except Exception as e:
                            results['errors'].append({
                                'type': 'row',
                                'row': index + 2,
                                'message': str(e),
                                'data': row.to_dict()
                            })

                    return render(request, 'core/import_item_results.html', {
                        'employee': employee,
                        'results': results
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