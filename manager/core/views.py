import json
from xmlrpc.client import Boolean
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .models import Employee, Position, Norm, Issue, PPEType
from users.models import CustomUser
from django.core.paginator import Paginator
from django.utils import timezone
# from .forms import ItemForm
from django.contrib.auth.decorators import login_required
from dateutil.relativedelta import relativedelta
from collections import defaultdict
from datetime import datetime, date, timedelta
import openpyxl
import logging
from .forms import EmployeeForm, PositionForm, NormCreateForm, IssueCreateForm
from django.urls import reverse
from django.http import JsonResponse


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
def list_items(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    # Получаем все выдачи (issues) вместо items
    issues = Issue.objects.filter(employee=employee)
    return render(request, 'core/list_items.html', {
        'issues': issues,  # Передаем issues вместо items
        'employee': employee
    })

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

from django.shortcuts import get_object_or_404, render

@login_required
def employee_detail(request, employee_id):
    employee = get_object_or_404(Employee, pk=employee_id)
    issues = Issue.objects.filter(employee=employee)
    return render(request, 'core/employee_detail.html', {'employee': employee, 'issues': issues})

from django.shortcuts import get_object_or_404, redirect, render
from django.contrib import messages
from django.views.decorators.http import require_http_methods
from django.contrib.auth.decorators import login_required
from .models import Norm, Position

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