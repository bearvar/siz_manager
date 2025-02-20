import json
from xmlrpc.client import Boolean
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .models import Employee, Item, Issue, Norm, Position
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
from .forms import EmployeeForm, PositionForm, NormCreateForm
from django.urls import reverse


logger = logging.getLogger(__name__)

@login_required
def position_list(request):
    positions = Position.objects.all()
    return render(request, 'core/position_list.html', {'positions': positions})

def index(request):
    title = "Главная страница"
    
    # Получаем все активные выдачи СИЗ с предзагрузкой связанных объектов
    issue_list = Issue.objects.select_related('employee', 'item').filter(is_active=True).order_by('employee', '-issue_date')
    
    # Группируем выдачи по сотрудникам
    grouped_issues = defaultdict(list)
    for issue in issue_list:
        grouped_issues[issue.employee].append(issue)
    
    context = {
        'title': title,
        'grouped_issues': dict(grouped_issues),
        'user': request.user,
        'current_date': timezone.now().date()
    }
    return render(request, 'core/index.html', context)


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
        form = NormCreateForm(request.POST, instance=Norm(position=position))
        if form.is_valid():
            norm = form.save()
            return redirect('core:position_detail', position_id=position.id)
    else:
        form = NormCreateForm(instance=Norm(position=position))

    context = {
        'title': f'Добавление нормы для {position.position_name}',
        'form': form,
        'position': position
    }
    return render(request, 'core/create_norm.html', context)

@login_required
def position_detail(request, position_id):
    position = get_object_or_404(Position, pk=position_id)
    norms = Norm.objects.filter(position=position)
    return render(request, 'core/position_detail.html', {'position': position, 'norms': norms})
