from django import template
import json
from django.core.serializers.json import DjangoJSONEncoder

register = template.Library()

@register.filter(name='to_json')
def to_json(value):
    return json.dumps({
        'id': value.id,
        'username': value.username,
        'email': value.email,
        'first_name': value.first_name,
        'last_name': value.last_name,
        'is_staff': value.is_staff,
        'is_active': value.is_active
    }, cls=DjangoJSONEncoder)