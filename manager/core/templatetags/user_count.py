from django import template
from django.utils import timezone
from users.models import CustomUser

register = template.Library()

@register.simple_tag
def get_active_user_count():
    return CustomUser.objects.filter(
        is_active=True,
        last_activity__gte=timezone.now() - timezone.timedelta(minutes=5)
    ).count()
