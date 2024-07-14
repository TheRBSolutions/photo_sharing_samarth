from django import template  # type: ignore
import re

register = template.Library()

@register.filter(name='endswith')
def endswith(value, arg):
    return value.endswith(arg)

@register.filter
def slugify(value):
    value = re.sub(r'\s+', '-', value)
    value = re.sub(r'[^a-zA-Z0-9\-]', '', value)
    return value.lower()