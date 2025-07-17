from django.contrib.auth.decorators import login_required

from django.shortcuts import render
from django.http import HttpResponse
from .models import Employe
import pandas as pd
from datetime import date

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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

@login_required
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
@login_required
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
    
@login_required
def liste_responsables_par_entite(request):
    entite_choisie = request.GET.get('entite')
    
    toutes_les_entites = [
        "Antenne d'Aru", "Antenne de Beni", "Antenne de Bumba", "Antenne de Dilolo", "Antenne de Fizi",
        "Antenne de Gungu", "Antenne de Kabare", "Antenne de Kalima", "Antenne de Kasenga", "Antenne de Kipushi",
        "Antenne de Masisi", "Antenne de Muanda", "Antenne de Mweka", "Antenne de Pweto", "Antenne de Rutshuru",
        "Antenne de Sandoa", "Antenne de Tshimbulu", "Antenne de Watsa", "Antenne d'Idiofa", "Bureau de Boende",
        "Bureau de Buta", "Bureau de Butembo", "Bureau de Gbadolite", "Bureau de Gemena", "Bureau de Kabinda",
        "Bureau de Kasaji", "Bureau de Lisala", "Bureau de Lodja", "Bureau de Mwene-Ditu", "Bureau de Tshikapa",
        "Bureau d'Ilebo", "Bureau d'Inongo", "Bureau d'Isiro", "Centre Médical Matonge", "Collège d’Experts",
        "Corps de Surveillance", "CP Commerce/Duk-Nord", "CP Kimbanseke/Duk-Est", "CP Kinshasa/Duk-Centre",
        "CP Lemba/Duk-Sud", "CP Makala/Duk-Centre", "CP Révolution/Duk-Nord", "Dir. de la Gestion Imm-Est",
        "Dir. de la Gestion Imm-Ouest", "Dir. des Etudes et Organisation", "Dir. des Ressources Humaines",
        "Dir. Urbaine de Kin Centre-Ouest", "Dir. Urbaine de Kin Nord-Est", "Dir. Urbaine de Kin Sud-Est",
        "Dir. Urbaine de Kin-Centre", "Dir. Urbaine de Kin-Est", "Dir. Urbaine de Kin-Nord",
        "Dir. Urbaine de Kin-Ouest", "Dir. Urbaine de Kin-Sud", "Direction de Formation",
        "Direction de l'Action San et Soc", "Direction de l'Audit Interne", "Direction de Prévention",
        "Direction de Recouvrement", "Direction des Services Généraux", "Direction Financière",
        "Direction Juridique", "Direction Technique", "DP Bandundu", "DP Boma", "DP Bukavu", "DP Bunia",
        "DP Goma", "DP Kamina", "DP Kananga", "DP Kasumbalesa", "DP Kikwit", "DP Kisangani", "DP Kolwezi",
        "DP Likasi", "DP Lubumbashi", "DP Maniema", "DP Matadi", "DP Mbandaka", "DP Mbanza-Ngungu",
        "DP Mbuji Mayi", "DP Tanganyika", "DP Uvira", "Pompes Funèbres Pop", "Secrétariat des Organes Statutaires",
        "Secrétariat du DG"
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
@login_required
def liste_controleurs(request):
    entite_choisie = request.GET.get('entite')

    toutes_les_entites = [
        "Antenne d'Aru", "Antenne de Beni", "Antenne de Bumba", "Antenne de Dilolo", "Antenne de Fizi",
        "Antenne de Gungu", "Antenne de Kabare", "Antenne de Kalima", "Antenne de Kasenga", "Antenne de Kipushi",
        "Antenne de Masisi", "Antenne de Muanda", "Antenne de Mweka", "Antenne de Pweto", "Antenne de Rutshuru",
        "Antenne de Sandoa", "Antenne de Tshimbulu", "Antenne de Watsa", "Antenne d'Idiofa", "Bureau de Boende",
        "Bureau de Buta", "Bureau de Butembo", "Bureau de Gbadolite", "Bureau de Gemena", "Bureau de Kabinda",
        "Bureau de Kasaji", "Bureau de Lisala", "Bureau de Lodja", "Bureau de Mwene-Ditu", "Bureau de Tshikapa",
        "Bureau d'Ilebo", "Bureau d'Inongo", "Bureau d'Isiro", "Centre Médical Matonge", "Collège d’Experts",
        "Corps de Surveillance", "CP Commerce/Duk-Nord", "CP Kimbanseke/Duk-Est", "CP Kinshasa/Duk-Centre",
        "CP Lemba/Duk-Sud", "CP Makala/Duk-Centre", "CP Révolution/Duk-Nord", "Dir. de la Gestion Imm-Est",
        "Dir. de la Gestion Imm-Ouest", "Dir. des Etudes et Organisation", "Dir. des Ressources Humaines",
        "Dir. Urbaine de Kin Centre-Ouest", "Dir. Urbaine de Kin Nord-Est", "Dir. Urbaine de Kin Sud-Est",
        "Dir. Urbaine de Kin-Centre", "Dir. Urbaine de Kin-Est", "Dir. Urbaine de Kin-Nord",
        "Dir. Urbaine de Kin-Ouest", "Dir. Urbaine de Kin-Sud", "Direction de Formation",
        "Direction de l'Action San et Soc", "Direction de l'Audit Interne", "Direction de Prévention",
        "Direction de Recouvrement", "Direction des Services Généraux", "Direction Financière",
        "Direction Juridique", "Direction Technique", "DP Bandundu", "DP Boma", "DP Bukavu", "DP Bunia",
        "DP Goma", "DP Kamina", "DP Kananga", "DP Kasumbalesa", "DP Kikwit", "DP Kisangani", "DP Kolwezi",
        "DP Likasi", "DP Lubumbashi", "DP Maniema", "DP Matadi", "DP Mbandaka", "DP Mbanza-Ngungu",
        "DP Mbuji Mayi", "DP Tanganyika", "DP Uvira", "Pompes Funèbres Pop", "Secrétariat des Organes Statutaires",
        "Secrétariat du DG"
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
@login_required
def export_employes_excel_complet(request):
    # Récupérer tous les employés avec tous les champs
    employes = Employe.objects.all().values()
    
    # Créer un DataFrame avec toutes les colonnes
    df = pd.DataFrame(employes).fillna('-')
    
    # Créer une réponse HTTP avec le fichier Excel
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liste_employes_complete.xlsx'
    df.to_excel(response, index=False)
    
    return response

@login_required
def export_employes_excel(request):
    employes = Employe.objects.all().values('nom', 'prenom', 'matricule', 'grade_actuel', 'sexe', 'service', 'fonction', 'statut', 'entite')
    df = pd.DataFrame(employes).fillna('-')
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename=liste_employes.xlsx'
    df.to_excel(response, index=False)
    return response
