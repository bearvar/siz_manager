# core/templatetags/user_filters.py
from django import template


# В template.Library зарегистрированы все встроенные теги и фильтры 
# шаблонов; добавляем к ним наш фильтр.
register = template.Library()


@register.filter
def addclass(field, css):
    if field == '':
        return ''
    else:
        return field.as_widget(attrs={'class': css})
