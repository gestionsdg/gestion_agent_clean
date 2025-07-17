from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from datetime import date
from .models import Employe

ordre_fonctions = [
    'Coordonnateur',
    'Coordonnateur a.i',
    'Coordonnateur Adjoint',
    'Coordonnateur Adjoint Technique',
    'Coordonnateur Adjoint Administratif',
    'Contrôleur'
]

def fonction_priority(fonction):
    try:
        return ordre_fonctions.index(fonction)
    except ValueError:
        return len(ordre_fonctions)

def calcul_age(naissance):
    if naissance:
        today = date.today()
        age = today.year - naissance.year - ((today.month, today.day) < (naissance.month, naissance.day))
        return age
    return "-"

@login_required
def liste_controleurs_par_entite(request):
    entite_choisie = request.GET.get('entite')
    toutes_les_entites = Employe.objects.filter(service__icontains='Contrôle').values_list('entite', flat=True).distinct()

    if entite_choisie:
        agents = Employe.objects.filter(service__icontains='Contrôle', entite=entite_choisie)
        titre = f"Liste des Contrôleurs : {entite_choisie}"
    else:
        agents = Employe.objects.filter(service__icontains='Contrôle')
        titre = "Liste des Contrôleurs"

    agents_prioritaires = [emp for emp in agents if emp.fonction in ordre_fonctions]
    autres_agents = [emp for emp in agents if emp.fonction not in ordre_fonctions]

    agents_prioritaires = sorted(agents_prioritaires, key=lambda emp: fonction_priority(emp.fonction))
    autres_agents = sorted(autres_agents, key=lambda emp: emp.nom or '')
    agents = agents_prioritaires + autres_agents

    donnees = []
    for idx, emp in enumerate(agents, 1):
        age = calcul_age(emp.date_naissance)
        duree_affectation = "-"
        if emp.date_affectation:
            today = date.today()
            delta = today.year - emp.date_affectation.year
            if (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day):
                delta -= 1
            duree_affectation = f"{delta} an{'s' if delta > 1 else ''}"

        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.fonction or '-',
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            age,
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree_affectation,
            emp.entite or '-'
        ])

    colonnes = [
        'N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Fonction',
        'Date naissance', 'Âge', 'Date affectation', 'Durée affectation', 'Entité'
    ]

    return render(request, 'personnel/liste_controleurs.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': toutes_les_entites,
        'selected_entite': entite_choisie
    })