from django.shortcuts import render
from django.http import HttpResponse
from .models import Employe
import pandas as pd
from datetime import date
from django.urls import path
from .views_export import liste_effectif_par_entite 

# -------------------------
# VUES EXPORT (Listes et Excel)
# -------------------------

def liste_actifs_par_entite(request):
    entite_choisie = request.GET.get('entite')
    toutes_les_entites = Employe.objects.filter(statut='Actif').values_list('entite', flat=True).distinct()

    if entite_choisie:
        agents = Employe.objects.filter(statut='Actif', entite=entite_choisie).order_by('nom')
        titre = f"Liste des Agents Actifs de {entite_choisie}"
    else:
        agents = Employe.objects.filter(statut='Actif').order_by('nom')
        titre = "Liste des Agents Actifs par Entité"

    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = "-"
        if emp.date_affectation:
            today = date.today()
            delta = today.year - emp.date_affectation.year
            if (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day):
                delta -= 1
            duree = f"{delta} an{'s' if delta > 1 else ''}"
        
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.sexe or '-',
            emp.date_engagement.strftime('%d/%m/%Y') if emp.date_engagement else '-',
            emp.grade_actuel or '-',
            emp.service or '-',
            emp.fonction or '-',
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree,
            emp.entite or '-'
        ])

    colonnes = ['N°', 'Nom', 'Matricule', 'Sexe', 'Date engagement', 'Grade actuel', 'Service', 'Fonction', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_actifs_par_entite.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': toutes_les_entites,
        'entite_choisie': entite_choisie
    })


def liste_decedes(request):
    agents = Employe.objects.filter(statut='Décédé').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        age_au_deces = "-"
        if emp.date_naissance and emp.date_statut:
            age = emp.date_statut.year - emp.date_naissance.year
            if (emp.date_statut.month, emp.date_statut.day) < (emp.date_naissance.month, emp.date_naissance.day):
                age -= 1
            age_au_deces = f"{age} an{'s' if age > 1 else ''}"
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            age_au_deces,
            emp.entite or '-'
        ])
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Date naissance', 'Date décès', 'Âge au décès', 'Entité']
    return render(request, 'personnel/liste_decedes.html', {'titre': 'Liste des Agents Décédés', 'colonnes': colonnes, 'donnees': donnees})


def liste_retraites(request):
    agents = Employe.objects.filter(statut__icontains='retraite').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        age_retraite = "-"
        duree_carriere = "-"
        if emp.date_naissance and emp.date_statut:
            age = emp.date_statut.year - emp.date_naissance.year
            if (emp.date_statut.month, emp.date_statut.day) < (emp.date_naissance.month, emp.date_naissance.day):
                age -= 1
            age_retraite = f"{age} an{'s' if age > 1 else ''}"
        if emp.date_engagement and emp.date_statut:
            duree = emp.date_statut.year - emp.date_engagement.year
            if (emp.date_statut.month, emp.date_statut.day) < (emp.date_engagement.month, emp.date_engagement.day):
                duree -= 1
            duree_carriere = f"{duree} an{'s' if duree > 1 else ''}"
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.sexe or '-',
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            age_retraite,
            emp.date_engagement.strftime('%d/%m/%Y') if emp.date_engagement else '-',
            duree_carriere,
            emp.entite or '-'
        ])
    colonnes = ['N°', 'Nom', 'Matricule', 'Sexe', 'Date de naissance', 'Date départ à la retraite', 'Âge départ', 'Date engagement', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_retraites.html', {'titre': 'Liste des Agents Retraités', 'colonnes': colonnes, 'donnees': donnees})


def liste_demis(request):
    agents = Employe.objects.filter(statut__icontains='démission').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree_carriere = "-"
        if emp.date_engagement and emp.date_statut:
            duree = emp.date_statut.year - emp.date_engagement.year
            if (emp.date_statut.month, emp.date_statut.day) < (emp.date_engagement.month, emp.date_engagement.day):
                duree -= 1
            duree_carriere = f"{duree} an{'s' if duree > 1 else ''}"
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_engagement.strftime('%d/%m/%Y') if emp.date_engagement else '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            duree_carriere,
            emp.entite or '-'
        ])
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Date engagement', 'Date démission', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_demis.html', {'titre': 'Liste des Agents Démissionnaires', 'colonnes': colonnes, 'donnees': donnees})


def liste_detaches(request):
    agents = Employe.objects.filter(statut__icontains='détachement').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            emp.entite or '-'
        ])
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Date détachement', 'Entité']
    return render(request, 'personnel/liste_detaches.html', {'titre': 'Liste des Agents en Détachement', 'colonnes': colonnes, 'donnees': donnees})


def liste_licencies(request):
    agents = Employe.objects.filter(statut__icontains='Licencié').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree_carriere = "-"
        if emp.date_engagement and emp.date_statut:
            duree = emp.date_statut.year - emp.date_engagement.year
            if (emp.date_statut.month, emp.date_statut.day) < (emp.date_engagement.month, emp.date_engagement.day):
                duree -= 1
            duree_carriere = f"{duree} an{'s' if duree > 1 else ''}"
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_engagement.strftime('%d/%m/%Y') if emp.date_engagement else '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            duree_carriere,
            emp.entite or '-'
        ])
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Date engagement', 'Date licenciement', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_licencies.html', {'titre': 'Liste des Agents Licenciés', 'colonnes': colonnes, 'donnees': donnees})


def liste_disponibilites(request):
    agents = Employe.objects.filter(statut__icontains='disponibilité').order_by('nom')

    donnees = []
    for idx, emp in enumerate(agents, 1):
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            emp.entite or '-'
        ])

    colonnes = [
        'N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
        'Date mise en disponibilité', 'Entité'
    ]

    return render(request, 'personnel/liste_disponibilites.html', {
        'titre': 'Liste des Agents en Disponibilité',
        'colonnes': colonnes,
        'donnees': donnees
    })


def liste_responsables_par_entite(request):
    entite_choisie = request.GET.get('entite')
    
    toutes_les_entites = [
        # liste des entités (inchangée)
    ]

    if entite_choisie:
        agents = Employe.objects.filter(fonction__icontains='responsable', entite=entite_choisie).order_by('nom')
        titre = f"Liste des Responsables du Service : {entite_choisie}"
    else:
        agents = Employe.objects.filter(fonction__icontains='responsable').order_by('nom')
        titre = "Liste des Responsables du Service"

    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = "-"
        if emp.date_affectation:
            today = date.today()
            delta = today.year - emp.date_affectation.year
            if (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day):
                delta -= 1
            duree = f"{delta} an{'s' if delta > 1 else ''}"
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.service or '-',
            emp.fonction or '-',
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree,
            emp.entite or '-'
        ])

    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
    'Service', 'Fonction', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_responsables.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': toutes_les_entites,
        'entite_choisie': entite_choisie
    })


def liste_controleurs(request):
    entite_choisie = request.GET.get('entite')

    toutes_les_entites = [
        # liste des entités (inchangée)
    ]

    if entite_choisie:
        agents = Employe.objects.filter(service__icontains='contrôle', entite=entite_choisie).order_by('nom')
        titre = f"Liste des Contrôleurs : {entite_choisie}"
    else:
        agents = Employe.objects.filter(service__icontains='contrôle').order_by('nom')
        titre = "Liste des Contrôleurs"

    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = "-"
        if emp.date_affectation:
            today = date.today()
            delta = today.year - emp.date_affectation.year
            if (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day):
                delta -= 1
            duree = f"{delta} an{'s' if delta > 1 else ''}"

        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.fonction or '-',
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree,
            emp.entite or '-'
        ])

    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe', 'Fonction', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_controleurs.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': toutes_les_entites,
        'entite_choisie': entite_choisie
    })


def export_employes_excel_complet(request):
    employes = Employe.objects.all().values()
    df = pd.DataFrame(employes).fillna('-')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liste_employes_complete.xlsx'
    df.to_excel(response, index=False)
    return response


def export_employes_excel(request):
    employes = Employe.objects.all().values('nom', 'prenom', 'matricule', 'grade_actuel', 'sexe', 'service', 'fonction', 'statut', 'entite')
    df = pd.DataFrame(employes).fillna('-')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liste_employes.xlsx'
    df.to_excel(response, index=False)
    return response

# -------------------------
# URLPATTERNS
# -------------------------

urlpatterns = [
    path('liste_actifs_par_entite/', liste_actifs_par_entite, name='liste_actifs_par_entite'),
    path('liste_decedes/', liste_decedes, name='liste_decedes'),
    path('liste_retraites/', liste_retraites, name='liste_retraites'),
    path('liste_demis/', liste_demis, name='liste_demis'),
    path('liste_detaches/', liste_detaches, name='liste_detaches'),
    path('liste_licencies/', liste_licencies, name='liste_licencies'),
    path('liste_disponibilites/', liste_disponibilites, name='liste_disponibilites'),
    path('liste_responsables_par_entite/', liste_responsables_par_entite, name='liste_responsables_par_entite'),
    path('liste_controleurs/', liste_controleurs, name='liste_controleurs'),
    path('export_employes_excel_complet/', export_employes_excel_complet, name='export_employes_excel_complet'),
    path('export_employes_excel/', export_employes_excel, name='export_employes_excel'),
    path('liste_effectif_par_entite/', liste_effectif_par_entite, name='liste_effectif_par_entite'),
]
# Vue HTML (navigateur)
def effectif_detaille_par_grade(request):
    # Liste des grades dans l'ordre défini
    GRADES_ORDONNES = [
        "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service",
        "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt", "Agent Aux 1ère Cl",
        "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
    ]

    # Récupérer toutes les entités distinctes
    entites = Employe.objects.values_list('entite', flat=True).distinct()

    # Récupérer l'entité choisie
    entite_choisie = request.GET.get("entite")

    if entite_choisie:
        data = []
        total_general = 0

        # Calcul effectif par grade
        for idx, grade in enumerate(GRADES_ORDONNES, start=1):
            count = Employe.objects.filter(entite=entite_choisie, grade_actuel=grade).count()
            data.append({
                "numero": idx,
                "grade": grade,
                "effectif": count
            })
            total_general += count

        return render(request, "personnel/effectif_par_grade.html", {
            "titre": f"Effectif des agents par grade : {entite_choisie}",
            "data": data,
            "total_general": total_general,
            "entites": entites,
            "entite_choisie": entite_choisie
        })
    else:
        # Si aucune entité sélectionnée, afficher juste le formulaire
        return render(request, "personnel/effectif_par_grade.html", {
            "entites": entites
        })


# Vue PDF
def effectif_detaille_par_grade_pdf(request):
    GRADES_ORDONNES = [
        "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service",
        "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt", "Agent Aux 1ère Cl",
        "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
    ]

    entite_choisie = request.GET.get("entite")
    if not entite_choisie:
        return redirect("effectif_detaille_par_grade")

    # Calcul effectif par grade
    data = []
    total_general = 0
    for idx, grade in enumerate(GRADES_ORDONNES, start=1):
        count = Employe.objects.filter(entite=entite_choisie, grade_actuel=grade).count()
        data.append({
            "numero": idx,
            "grade": grade,
            "effectif": count
        })
        total_general += count

    # Rendu PDF
    html_string = render_to_string("personnel/effectif_par_grade_pdf.html", {
        "titre": f"Effectif des agents par grade : {entite_choisie}",
        "data": data,
        "total_general": total_general
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=effectif_par_grade.pdf"
    HTML(string=html_string).write_pdf(response, stylesheets=[CSS(string="@page { size: portrait; }")])
    return response
