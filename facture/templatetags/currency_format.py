from babel.numbers import format_currency
from django import template

register = template.Library()

@register.filter
def local_currency(value, currency='USD'):
    try:
        return format_currency(value, currency, locale='en_US')
    except (ValueError, TypeError):
        return value
