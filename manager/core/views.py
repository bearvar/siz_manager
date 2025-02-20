import json
from xmlrpc.client import Boolean
from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponseRedirect
from .models import Employee, Item, Issue, Norm
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
from .forms import EmployeeForm, PositionForm


logger = logging.getLogger(__name__)

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
def item_create(request):
    if request.method == 'POST':
        form_name = request.POST.get('form_name', '')
        
        # Handle manual form submission
        form = ItemForm(request.POST)
        if form.is_valid():
            item = form.save(commit=False)
            item.author = request.user
            item.save()
            logger.info(f"Created new item: {item}")
            return redirect('items:profile', username=request.user.username)
        else:
            logger.error(f"Form is not valid: {form.errors}")
            return render(request, 'items/create_item.html', {'form': form})

    # GET request case - render an empty form
    else:
        form = ItemForm()
        return render(request, 'items/create_item.html', {'form': form})
