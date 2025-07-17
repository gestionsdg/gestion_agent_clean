from django import template

register = template.Library()

@register.filter
def clean_nan(value):
    if value is None or str(value).strip().lower() == "nan" or str(value).strip() == "":
        return "-"
    return value
