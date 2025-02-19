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
