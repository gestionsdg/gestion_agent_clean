# personnel/vue_effectif_controleurs.py
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Employe

THRESHOLD_AGE = 55


def _age(date_naissance, ref=None):
    """Âge en années révolues (None si inconnu)."""
    if not date_naissance:
        return None
    ref = ref or date.today()
    return ref.year - date_naissance.year - (
        (ref.month, ref.day) < (date_naissance.month, date_naissance.day)
    )


@login_required
def tableau_controleurs_cnss(request):
    """
    Regroupe les contrôleurs par tranche d'âge :
      - moins_de_55 : âge < 55
      - plus_de_54  : âge >= 55
    Inclut les variantes d'orthographe/accent (Contrôle/Controle, Contrôleur/Controleur).
    """
    fonctions_cible = [
        "Coordonnateur",
        "Coordonnateur a.i",
        "Coordonnateur Adjoint",
        "Coordonnateur Adjoint Technique",
        "Coordonnateur Adjoint Administratif",
        "Contrôleur",
        "Controleur",  # variante sans accent
    ]

    # Contrôle via service OU via fonction (avec tolérance aux accents)
    filtre_controle = (
        Q(service__icontains="Contrôle")
        | Q(service__icontains="Controle")
        | Q(fonction__in=fonctions_cible)
        | Q(fonction__icontains="Contrôleur")
        | Q(fonction__icontains="Controleur")
    )

    # Tri lisible: entité > nom > prénom
    employes = (
        Employe.objects.filter(filtre_controle).order_by("entite", "nom", "prenom")
    )

    moins_de_55, plus_de_54, age_inconnu = [], [], []

    today = date.today()
    for emp in employes:
        age = _age(emp.date_naissance, today)
        emp.age = age  # utile dans le template
        if age is None:
            age_inconnu.append(emp)
        elif age < THRESHOLD_AGE:
            moins_de_55.append(emp)
        else:
            plus_de_54.append(emp)

    # Total "comptable" = connus uniquement (comme votre version initiale)
    total = len(moins_de_55) + len(plus_de_54)

    return render(
        request,
        "personnel/effectif_controleurs_cnss.html",
        {
            "moins_de_55": moins_de_55,
            "plus_de_54": plus_de_54,
            "age_inconnu": age_inconnu,  # optionnel: à ignorer si non utilisé
            "total": total,
            "seuil_age": THRESHOLD_AGE,
            "titre": "Effectif des contrôleurs CNSS",
        },
    )
