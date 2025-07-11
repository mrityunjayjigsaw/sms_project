from django import template

register = template.Library()

@register.filter
def startswith(value, arg):
    """Usage: {{ value|startswith:"Posted fee" }} returns True/False"""
    return str(value).startswith(arg)
