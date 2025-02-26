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
from .forms import EmployeeForm, IssueCreateForm, NormCreateForm, PositionForm
from .models import Employee, Issue, Norm, PPEType, Position
from users.models import CustomUser
from xmlrpc.client import Boolean
from django.views.decorators.http import require_http_methods
from django.template.defaulttags import register


logger = logging.getLogger(__name__)


def index(request):
    title = "Главная страница"
    
    # Получаем все активные выдачи СИЗ с предзагрузкой связанных объектов
    # issue_list = Issue.objects.select_related('employee', 'item').filter(is_active=True).order_by('employee', '-issue_date')
    
    # Группируем выдачи по сотрудникам
    # grouped_issues = defaultdict(list)
    # for issue in issue_list:
    #     grouped_issues[issue.employee].append(issue)
    
    context = {
        'title': title,
        # 'grouped_issues': dict(grouped_issues),
        # 'user': request.user,
        'current_date': timezone.now().date()
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
            form.save()
            return redirect('core:index')  # Redirect to the index page after successful creation
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
    all_issues = Issue.objects.filter(employee=employee).order_by(
        'expiration_date' # Сначала NULL, потом по возрастанию даты
    )
    norms_status = []
    
    if employee.position:
        today = date.today()
        norms = Norm.objects.filter(position=employee.position).select_related('ppe_type')
        
        for norm in norms:
            ppe_issues = all_issues.filter(
                ppe_type=norm.ppe_type,
                is_active=True
            )
            
            # Актуальные выдачи (не просроченные)
            valid_issues = ppe_issues.filter(
                Q(expiration_date__gte=today) | 
                Q(expiration_date__isnull=True)
            )
            valid_count = valid_issues.count()
            
            # Статусные флаги
            status = []
            expired_exists = ppe_issues.filter(expiration_date__lt=today).exists()
            shortage = valid_count < norm.quantity
            excess = valid_count > norm.quantity
            
            if expired_exists:
                status.append("⛔ Просрочено")
            if shortage:
                status.append(f"❗ Не хватает ({valid_count}/{norm.quantity})")
            if excess:
                status.append(f"📦 Лишние ({valid_count - norm.quantity} шт.)")
            
            # Определение общего статуса
            final_status = " | ".join(status) if status else "✅ В норме"
            
            norms_status.append({
                'ppe_type': norm.ppe_type.name,
                'required': norm.quantity,
                'actual': valid_count,
                'status': final_status
            })
    
    context = {
        'employee': employee,
        'issues': all_issues,
        'norms_status': sorted(norms_status, key=lambda x: x['status'], reverse=True)
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
            ppe_type = form.cleaned_data['ppe_type']
            norm = Norm.objects.get(position=employee.position, ppe_type=ppe_type)
            
            # Создаем Issue без явного указания lifespan
            for _ in range(form.cleaned_data['quantity']):
                Issue.objects.create(
                    employee=employee,
                    ppe_type=ppe_type,
                    item_name=form.cleaned_data['item_name'],
                    issue_date=form.cleaned_data['issue_date'],
                    item_size=form.cleaned_data['item_size'],
                    item_mu=ppe_type.default_mu
                )
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
    issue = get_object_or_404(Issue.objects.select_related('employee', 'ppe_type'), pk=issue_id)
    employee_id = issue.employee.id
    
    try:
        # Получаем данные из формы
        item_name = request.POST.get('item_name', '').strip()
        item_size = request.POST.get('item_size', '').strip() or None
        issue_date_str = request.POST.get('issue_date')
        expiration_date_str = request.POST.get('expiration_date')

        # Валидация обязательных полей
        if not issue_date_str:
            raise ValueError("Дата выдачи обязательна для заполнения")

        # Парсим даты
        new_issue_date = datetime.strptime(issue_date_str, '%Y-%m-%d').date()
        new_expiration_date = (
            datetime.strptime(expiration_date_str, '%Y-%m-%d').date() 
            if expiration_date_str 
            else None
        )

        # Сохраняем оригинальные значения для сравнения
        original_issue_date = issue.issue_date
        original_expiration_date = issue.expiration_date

        # Логика пересчёта expiration_date
        if not expiration_date_str or new_expiration_date == original_expiration_date:
            if new_issue_date != original_issue_date:
                try:
                    norm = Norm.objects.get(
                        position=issue.employee.position,
                        ppe_type=issue.ppe_type
                    )
                    new_expiration_date = new_issue_date + relativedelta(months=norm.lifespan)
                except Norm.DoesNotExist:
                    pass  # Оставляем текущее значение или None

        # Обновляем объект
        issue.item_name = item_name
        issue.item_size = item_size
        issue.issue_date = new_issue_date
        issue.expiration_date = new_expiration_date
        
        # Сохраняем изменения
        issue.save()
        
        messages.success(request, "Изменения успешно сохранены")
    except ValueError as ve:
        logger.error(f"Value error in issue_update: {str(ve)}")
        messages.error(request, f"Ошибка в данных: {str(ve)}")
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
            
            # Обработка размеров
            employee.body_size = request.POST.get('body_size')
            employee.head_size = request.POST.get('head_size')
            employee.glove_size = request.POST.get('glove_size')
            shoe_size = request.POST.get('shoe_size')
            employee.shoe_size = int(shoe_size) if shoe_size else None
            
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