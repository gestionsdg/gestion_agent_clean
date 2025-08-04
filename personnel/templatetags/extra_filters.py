from django import template

register = template.Library()

@register.filter
def clean_nan(value):
    if value is None or str(value).strip().lower() == "nan" or str(value).strip() == "":
        return "-"
    return value

@register.filter
def get_item(dictionary, key):
    """Récupère la valeur d'un dictionnaire avec la clé donnée"""
    return dictionary.get(key, "-")
