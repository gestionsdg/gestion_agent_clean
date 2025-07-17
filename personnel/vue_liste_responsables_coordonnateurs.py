from django.contrib.auth.decorators import login_required
from datetime import date
from django.shortcuts import render
from .models import Employe

@login_required
def liste_responsables_coordonnateurs(request):
    entite_choisie = request.GET.get('entite')

    fonctions_cibles = [
        "Responsable",
        "Responsable a.i",
        "Coordonnateur",
        "Coordonnateur a.i"
    ]

    fonctions_surbrillance_bleue = ["Responsable a.i", "Coordonnateur a.i"]
    grades_surbrillance_verte = ["Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur"]

    entites_disponibles = Employe.objects.filter(
        fonction__in=fonctions_cibles
    ).values_list("entite", flat=True).distinct()

    agents = Employe.objects.filter(fonction__in=fonctions_cibles)
    if entite_choisie:
        agents = agents.filter(entite=entite_choisie)
        titre = f"Liste des Responsables et Coordonnateurs du Service - {entite_choisie}"
    else:
        titre = "Liste des Responsables et Coordonnateurs du Service"

    donnees = []
    for idx, emp in enumerate(agents.order_by("nom"), 1):
        duree = "-"
        if emp.date_affectation:
            today = date.today()
            delta = today.year - emp.date_affectation.year
            if (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day):
                delta -= 1
            duree = f"{delta} an{'s' if delta > 1 else ''}"

        # Détermine la classe de surbrillance
        if emp.fonction in fonctions_surbrillance_bleue:
            row_class = "bg-fonction"
        elif emp.grade_actuel in grades_surbrillance_verte:
            row_class = "bg-grade"
        else:
            row_class = ""

        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.service or '-',
            emp.fonction or '-',
            emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else '-',
            duree,
            emp.entite or '-',
            row_class
        ])

    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Service', 'Fonction', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_responsables_coordonnateurs.html', {
        'donnees': donnees,
        'colonnes': colonnes,
        'titre': titre,
        'entites': entites_disponibles,
        'selected_entite': entite_choisie
    })
