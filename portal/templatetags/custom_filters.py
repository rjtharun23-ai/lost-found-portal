from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Custom filter to get dictionary value by key in templates.
    Usage: {{ dict|get_item:key }}
    """
    return dictionary.get(key)
