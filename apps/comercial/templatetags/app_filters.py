from django import template
from apps.hrm.models import Company
from django.template.loader import get_template

register = template.Library()


@register.filter(name='get')
def get(d, k):
    return d.get(k, None)


@register.filter(name='zfill')
def zfill(d, k):
    res = str(d).zfill(int(k))
    return res


@register.filter
def intcomma(value):
    return value + 1


@register.filter(name='calculate_percent')
def calculate_percent(cs, ct):
    res = 0
    if cs > 0:
        res = round(cs * 100 / ct)
    return res
