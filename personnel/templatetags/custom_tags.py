from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Récupère une valeur d’un dictionnaire avec une clé dynamique dans les templates.
    Exemple d’utilisation : {{ mon_dict|get_item:ma_cle }}
    """
    return dictionary.get(key, 0)
