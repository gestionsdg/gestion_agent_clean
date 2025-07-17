from django.contrib.auth.decorators import login_required
# personnel/vue_effectif_controleurs.py

from django.shortcuts import render
from datetime import date
from .models import Employe

@login_required
def tableau_controleurs_cnss(request):
    today = date.today()

    fonctions_cible = [
        "Coordonnateur", "Coordonnateur a.i", "Coordonnateur Adjoint",
        "Coordonnateur Adjoint Technique", "Coordonnateur Adjoint Administratif", 
        "Contrôleur"
    ]

    employes = Employe.objects.filter(service__icontains="contrôle", fonction__in=fonctions_cible)

    moins_de_55 = []
    plus_de_54 = []

    for emp in employes:
        if emp.date_naissance:
            age = today.year - emp.date_naissance.year - ((today.month, today.day) < (emp.date_naissance.month, emp.date_naissance.day))
            emp.age = age
            if age < 55:
                moins_de_55.append(emp)
            else:
                plus_de_54.append(emp)

    total = len(moins_de_55) + len(plus_de_54)

    return render(request, 'personnel/effectif_controleurs_cnss.html', {
        'moins_de_55': moins_de_55,
        'plus_de_54': plus_de_54,
        'total': total,
        'titre': "Effectif des contrôleurs CNSS"
    })
