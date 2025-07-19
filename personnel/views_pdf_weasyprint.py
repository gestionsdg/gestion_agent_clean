from datetime import date
from django.shortcuts import get_object_or_404
from django.template.loader import render_to_string
from django.http import HttpResponse
from django.utils.dateformat import DateFormat
from django.utils.timezone import now
from weasyprint import HTML, CSS
from django.db.models import Q
from .models import Employe
from django.http import HttpResponse
from collections import defaultdict
from weasyprint import HTML, CSS  # ✅ Assurez-vous que cette ligne est bien présente
from .utils import calcul_duree, format_duree  # Assurez-vous que ces fonctions sont bien définies
from django.utils.timezone import now

ordre_fonctions = [
    "Coordonnateur",
    "Coordonnateur a.i",
    "Coordonnateur Adjoint",
    "Coordonnateur Adjoint Technique",
    "Coordonnateur Adjoint Administratif",
    "Contrôleur"
]

def fonction_priority(fonction):
    try:
        return ordre_fonctions.index(fonction)
    except ValueError:
        return len(ordre_fonctions)

def calcul_age(date_naissance):
    if date_naissance:
        today = date.today()
        age = today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))
        return age
    return None

def calcul_duree(depuis):
    if depuis:
        today = date.today()
        delta = today.year - depuis.year - ((today.month, today.day) < (depuis.month, depuis.day))
        return delta
    return None

def format_duree(value):
    return f"{value} an{'s' if value > 1 else ''}" if value is not None else "-"


def fiche_employe_pdf(request, pk):
    employe = get_object_or_404(Employe, pk=pk)

    age = calcul_duree(employe.date_naissance)
    anciennete_societe = calcul_duree(employe.date_engagement)
    anciennete_grade = calcul_duree(employe.date_derniere_promotion)
    duree_affectation = calcul_duree(employe.date_affectation)
    duree_prise_fonction = calcul_duree(employe.date_prise_fonction)

    context = {
        'employe': employe,
        'age': format_duree(age),
        'anciennete_societe': format_duree(anciennete_societe),
        'anciennete_grade': format_duree(anciennete_grade),
        'duree_affectation': format_duree(duree_affectation),
        'duree_prise_fonction': format_duree(duree_prise_fonction),
        'date_impression': DateFormat(date.today()).format('d/m/Y'),
    }

    html_string = render_to_string('personnel/fiche_employe.html', context)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=fiche_{employe.matricule}.pdf'
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response
    
def liste_responsables_par_entite_pdf(request):
    entite = request.GET.get('entite')
    agents = Employe.objects.filter(
        Q(entite=entite) & (
            Q(fonction__icontains='responsable') | Q(fonction__icontains='coordonnateur')
        )
    ).order_by('nom')

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
            emp.service or '-',
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree,
            emp.entite or '-',
        ])

    titre = f"Liste des Responsables du Service : {entite}" if entite else "Liste des Responsables"

    html_string = render_to_string('personnel/liste_responsables_pdf.html', {
        'donnees': donnees,
        'titre': titre,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=responsables_{entite or "tous"}.pdf'
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response
    
def liste_controleurs_pdf(request):
    entite = request.GET.get('entite')
    if entite:
        agents = Employe.objects.filter(service__icontains='Contrôle', entite=entite)
    else:
        agents = Employe.objects.filter(service__icontains='Contrôle')

    # Ordre des fonctions et des grades
    ordre_fonctions = [
        "Coordonnateur",
        "Coordonnateur a.i",
        "Coordonnateur Adjoint",
        "Coordonnateur Adjoint Technique",
        "Coordonnateur Adjoint Technique a.i",
        "Coordonnateur Adjoint Administratif",
        "Coordonnateur Adjoint Administratif a.i",
        "Contrôleur"
    ]
    ordre_grades = [
        "Chef de Division", "Chef de Sce Ppal", "Chef de Service", "Chef de Sce Adjt",
        "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt"
    ]

    def classement(emp):
        fonction_index = ordre_fonctions.index(emp.fonction) if emp.fonction in ordre_fonctions else len(ordre_fonctions)
        grade_index = ordre_grades.index(emp.grade_actuel) if emp.grade_actuel in ordre_grades else len(ordre_grades)
        return (fonction_index, grade_index, emp.nom or '')

    agents = sorted(agents, key=classement)

    donnees = []
    for idx, emp in enumerate(agents, 1):
        age = calcul_age(emp.date_naissance)
        duree_aff = calcul_duree(emp.date_affectation)
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.fonction or '-',
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            age if age is not None else '-',
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            duree_aff if duree_aff is not None else '-',
            emp.entite or '-',
        ])

    titre = f"<u>Liste des contrôleurs : {entite}</u>" if entite else "<u>Liste des contrôleurs de la CNSS</u>"

    html_string = render_to_string('personnel/liste_controleurs_pdf.html', {
        'donnees': donnees,
        'titre': titre,
    })

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=controleurs_{entite or "tous"}.pdf'

    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { border: 1px solid black; padding: 5px; text-align: center; }
        th.left, td.left { text-align: left; }
    ''')

    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response

def liste_responsables_coordonnateurs_pdf(request):
    entite = request.GET.get('entite')
    grade_ordre = [
        "Directeur", "Sous-Directeur", "Chef de Division",
        "Chef de Sce Ppal", "Chef de Service", "Chef de Sce Adjt", "Chef de Section",
        "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt",
        "Agent Aux 1ère Cl", "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
    ]

    if entite:
        agents = Employe.objects.filter(
            fonction__in=["Responsable", "Responsable a.i", "Coordonnateur", "Coordonnateur a.i"],
            entite=entite
        )
    else:
        agents = Employe.objects.filter(
            fonction__in=["Responsable", "Responsable a.i", "Coordonnateur", "Coordonnateur a.i"]
        )

    agents = sorted(
        agents,
        key=lambda x: (
            grade_ordre.index(x.grade_actuel) if x.grade_actuel in grade_ordre else len(grade_ordre),
            x.nom or ""
        )
    )

    donnees = []
    for i, agent in enumerate(agents, start=1):
        if agent.date_affectation:
            nb_ans = calcul_duree(agent.date_affectation)
            if nb_ans <= 1:
                duree_str = f"{nb_ans} an"
            else:
                duree_str = f"{nb_ans} ans"
        else:
            duree_str = "-"
        
        donnees.append([
            i,
            agent.nom or "",
            agent.matricule or "",
            agent.grade_actuel or "",
            agent.sexe or "",
            agent.service or "",
            agent.fonction or "",
            agent.date_affectation.strftime("%d/%m/%Y") if agent.date_affectation else "-",
            duree_str
        ])

    html_string = render_to_string("personnel/liste_responsables_coordonnateurs_pdf.html", {
        "titre": f"Liste des Responsables et Coordonnateurs de Service - {entite}" if entite else "Liste des Responsables et Coordonnateurs de Service - Toutes Entités",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Service", "Fonction", "Date affectation", "Durée affectation"],
        "donnees": donnees,
        "entite": entite,
        "today": now()
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_responsables_coordonnateurs.pdf"
    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { border: 1px solid black; padding: 5px; text-align: center; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response
    
from collections import defaultdict

def liste_actifs_par_entite_pdf(request):
    entite = request.GET.get('entite', '').strip()

    print("🧪 Entité reçue :", entite)
    agents = Employe.objects.filter(entite=entite, statut="Actif").order_by('nom') if entite else []
    print("🧪 Nombre d'agents trouvés :", len(agents))

    grade_ordre = [
        "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service",
        "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
        "Commis Chef", "Commis Ppal", "Commis", "Commis Adjt",
        "Agent Aux 1ère Cl", "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
    ]

    # Groupe les agents par service, puis sépare Cadres et Agents
    groupes_services = defaultdict(lambda: {'cadres': [], 'agents': []})

    for emp in agents:
        service = emp.service or "Non défini"
        if emp.grade_actuel in ["Directeur", "Sous-Directeur"]:
            groupes_services[service]['cadres'].append(emp)
        else:
            groupes_services[service]['agents'].append(emp)

    donnees_groupes = []

    for service, groupes in sorted(groupes_services.items()):  # tri par nom de service
        # Trier les cadres
        
        def fonction_cadre_index(emp):
            priorites = [
                ("Assistant Principal/DG", 0),
                ("Directeur", 1),
                ("Directeur Provincial", 2),
                ("Assistant Administratif/DG", 3),
                ("Assistant Financier/DG", 4),
                ("Assistant Chargé de Recouvr./DG", 5),
                ("Assistant Chargé de Mission/DG", 6),
                ("Assistant Juridique/DG", 7),
                ("Assistant Technique/DG", 8),
                ("Assistant du DGA", 9),
                ("Sous-Directeur GESOC", 10),
                ("Sous-Directeur Pension Compl.", 11),
                ("Sous-Directeur de Trésorerie", 12),
                ("Sous-Directeur Log. et Maint.", 13),
                ("Sous-Directeur des Appro", 14),
                ("Sous-Directeur Juridique", 15),
                ("Sous-Directeur Contentieux", 16),
                ("Sous-Directeur de Grandes Entreprises", 17),
                ("Sous-Directeur des Statistiques", 18),
                ("Sous-Directeur du Contentieux", 19),
                ("Sous-Directeur Pharmacie et Labo", 20),
                ("Sous-Directeur Technique", 21),
                ("Sous-Directeur Adm. et Fin.", 22),
                ("Sous-Directeur", 23),
        ]

        cadres = sorted(
            groupes['cadres'],
            key=lambda x: (
                grade_ordre.index(x.grade_actuel) if x.grade_actuel in grade_ordre else len(grade_ordre),
                x.nom or ""
            )
        )
        lignes_cadres = []
        for i, emp in enumerate(cadres, 1):
            lignes_cadres.append([
            # Colonne Service supprimée pour Cadres
                i,
                emp.nom or "-",
                emp.matricule or "-",
                emp.sexe or "-",
                emp.grade_actuel or "-",
                
                emp.fonction or "-",
                emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
                format_duree(calcul_duree(emp.date_affectation)),
            ])

        # Trier les agents
               # Trier les agents
        ordre_fonctions_prioritaires = [
            "Responsable", "Responsable a.i",
            "Coordonnateur", "Coordonnateur a.i",
            "Coordonnateur Adjoint",
            "Coordonnateur Adjoint Technique", "Coordonnateur Adjoint Technique a.i",
            "Coordonnateur Adjoint Administratif", "Coordonnateur Adjoint Administratif a.i"
        ]

        def fonction_index(fonction):
            fonction = (fonction or "").strip().lower()
            for i, f in enumerate(ordre_fonctions_prioritaires):
                if fonction == f.lower():
                    return i
            return len(ordre_fonctions_prioritaires)

        agents_ = sorted(
            groupes['agents'],
            key=lambda x: (
                fonction_index(x.fonction),
                grade_ordre.index(x.grade_actuel) if x.grade_actuel in grade_ordre else len(grade_ordre),
                x.nom or ""
            )
        )

        lignes_agents = []
        for i, emp in enumerate(agents_, 1):
            lignes_agents.append([
                i,
                emp.nom or "-",
                emp.matricule or "-",
                emp.sexe or "-",
                emp.grade_actuel or "-",
                emp.fonction or "-",
                emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
                format_duree(calcul_duree(emp.date_affectation)),
            ])

        donnees_groupes.append((service, lignes_cadres, lignes_agents))

    html_string = render_to_string("personnel/liste_actifs_par_entite_pdf.html", {
        "titre": f"Liste des agents actifs : {entite}" if entite else "Liste des agents actifs",
        "entite": entite,
        "colonnes": ["N°", "Nom", "Matricule", "Sexe", "Grade actuel", "Fonction", "Date affectation", "Durée affectation"],
        "donnees_groupes": donnees_groupes,
        "today": now(),
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=actifs_{entite or 'tous'}.pdf"

    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; font-size: 16px; margin-bottom: 10px; }
        h3 { margin-top: 20px; font-size: 14px; }
        h4 { margin-top: 10px; font-size: 13px; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 5px; }
        th, td { border: 1px solid black; padding: 5px; }
        th { background-color: #eee; text-align: center; }
        td:nth-child(1), td:nth-child(3), td:nth-child(4), td:nth-child(8), td:nth-child(9) { text-align: center; }
        td:nth-child(2), td:nth-child(5), td:nth-child(6), td:nth-child(7) { text-align: left; }
    ''')

    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response
# Ajoutez ceci à la fin de votre fichier views_pdf_weasyprint.py
ordre_fonctions = [
    "Assistant Principal/DG", 
    "Directeur", 
    "Directeur Provincial",
    "Assistant Administratif/DG", 
    "Assistant Financier/DG", 
    "Assistant Chargé de Recouvr./DG", 
    "Assistant Chargé de Mission/DG", 
    "Assistant Juridique/DG", 
    "Assistant Technique/DG", 
    "Assistant du DGA",
    "Sous-Directeur GESOC",         
    "Sous-Directeur Pension Compl.",
    "Sous-Directeur de Trésorerie",
    "Sous-Directeur Log. et Maint.",
    "Sous-Directeur des Appro",
    "Sous-Directeur Juridique",
    "Sous-Directeur Contentieux",
    "Sous-Directeur de Grandes Entreprises",
    "Sous-Directeur des Statistiques",
    "Sous-Directeur du Contentieux",
    "Sous-Directeur Pharmacie et Labo",
    "Sous-Directeur Technique", 
    "Sous-Directeur Adm. et Fin.", 
    "Sous-Directeur", 
  
]

def fonction_priority(fonction):
    try:
        return ordre_fonctions.index(fonction)
    except ValueError:
        return len(ordre_fonctions)

def calcul_duree_texte(date_affectation):
    if date_affectation:
        today = date.today()
        duree = today.year - date_affectation.year - ((today.month, today.day) < (date_affectation.month, date_affectation.day))
        if duree <= 1:
            return f"{duree} an"
        else:
            return f"{duree} ans"
    return "-"

def format_age(age):
    if age is None:
        return "-"
    return f"{age} an" if age <= 1 else f"{age} ans"

def liste_cadres_direction_pdf(request):
    entite = request.GET.get('entite')
    cadres = Employe.objects.filter(
        statut='Actif',
        entite=entite,
        fonction__in=ordre_fonctions
    )

    # Trier selon la priorité de fonction
    cadres = sorted(cadres, key=lambda x: (fonction_priority(x.fonction), x.nom))

    lignes = []
    for i, agent in enumerate(cadres, start=1):
        age = calcul_age(agent.date_naissance)
        lignes.append((
            i,
            agent.nom,
            agent.matricule,
            agent.grade_actuel,
            agent.sexe,
            agent.fonction,
            agent.date_affectation.strftime('%d/%m/%Y') if agent.date_affectation else '-',
            calcul_duree_texte(agent.date_affectation),
            format_age(age)
        ))

    html_string = render_to_string("personnel/liste_cadres_direction_pdf.html", {
        'entite': entite,
        'lignes': lignes
    })

    css = CSS(string='''
        @page {
            size: A4 landscape;
            margin: 1cm;
        }
    ''')

    html = HTML(string=html_string)
    pdf = html.write_pdf(stylesheets=[css])

    return HttpResponse(pdf, content_type='application/pdf')

ordre_grades = [
    "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal", "Chef de Service", "Chef de Sce Adjt",
    "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt", "Commis Chef", "Commis Ppal", "Commis",
    "Commis Adjt", "Agent Aux 1ère Cl", "Agent Aux 2è Cl", "Manœuvre Sp", "Manœuvre Lourd", "Manœuvre Ord"
]

def grade_priority(grade):
    try:
        return ordre_grades.index(grade)
    except ValueError:
        return len(ordre_grades)

def calcul_age(date_naissance):
    if date_naissance:
        today = date.today()
        return today.year - date_naissance.year - (
            (today.month, today.day) < (date_naissance.month, date_naissance.day)
        )
    return None

def liste_retraitables_pdf(request):
    agents = Employe.objects.exclude(date_naissance__isnull=True)
    retraitables = []

    for agent in agents:
        age = calcul_age(agent.date_naissance)
        if age and 60 <= age <= 65:
            retraitables.append({
                'nom': agent.nom,
                'matricule': agent.matricule,
                'grade': agent.grade_actuel,
                'sexe': agent.sexe,
                'date_naissance': agent.date_naissance,
                'age': age,
                'age_str': f"{age} {'an' if age <= 1 else 'ans'}",
                'entite': agent.entite,
                'highlight': age == 65
            })

    retraitables.sort(key=lambda x: (x['age'], grade_priority(x['grade']), x['nom'].lower()))

    print("⚠️ Nombre d'agents retraitables trouvés :", len(retraitables))

    html_string = render_to_string("personnel/liste_retraitables_pdf.html", {
        'retraitables': retraitables,
        'date': date.today(),
    })

    html = HTML(string=html_string)
    css = CSS(string="@page { size: A4 landscape; }")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename=\"cadres_agents_retraitables.pdf\"'
    html.write_pdf(response, stylesheets=[css])
    return response

def liste_detaches_pdf(request):
    agents = Employe.objects.filter(statut="Détaché").order_by("nom")

    donnees = []
    for i, emp in enumerate(agents, start=1):
        donnees.append([
            i,
            emp.nom or "-",
            emp.matricule or "-",
            emp.grade_actuel or "-",
            emp.sexe or "-",
            emp.fonction or "-",
            emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
            format_duree(calcul_duree(emp.date_affectation)),
            emp.entite or "-"
        ])

    html_string = render_to_string("personnel/liste_detaches.html", {
        "titre": "Liste des agents en détachement",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Fonction", "Date affectation", "Durée affectation", "Entité"],
        "donnees": donnees,
    })

    css = CSS(string="""
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }
        th, td {
            border: 1px solid black;
            padding: 6px;
            text-align: center;
        }
        th.left, td.left {
            text-align: left;
        }
    """)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_detaches.pdf"
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response

def calcul_duree(depuis):
    if depuis:
        today = date.today()
        return today.year - depuis.year - ((today.month, today.day) < (depuis.month, depuis.day))
    return None

def liste_licencies_pdf(request):
    agents = Employe.objects.filter(statut="Licencié").order_by("nom")
    donnees = []
    for i, agent in enumerate(agents, start=1):
        donnee = [
            i,
            agent.nom,
            agent.matricule,
            agent.grade_actuel,
            agent.sexe,
            agent.date_engagement,
            agent.date_statut,
            calcul_duree(agent.date_engagement),
            agent.entite
        ]
        donnees.append(donnee)

    html_string = render_to_string("personnel/liste_licencies_pdf.html", {
        "titre": "Liste des Agents Licenciés",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Date engagement", "Date licenciement", "Carrière", "Entité"],
        "donnees": donnees,
    })

    html = HTML(string=html_string, base_url=request.build_absolute_uri())
    css = CSS(string='@page { size: landscape; }')
    pdf = html.write_pdf(stylesheets=[css])
    return HttpResponse(pdf, content_type='application/pdf')

def calcul_duree(depuis):
    if depuis:
        today = date.today()
        return today.year - depuis.year - ((today.month, today.day) < (depuis.month, depuis.day))
    return None

def liste_disponibilite_pdf(request):
    agents = Employe.objects.filter(statut="Mise en disponibilité").order_by('nom')
    donnees = {}
    for i, agent in enumerate(agents, start=1):
        if agent.date_statut:
            today = date.today()
            delta = today.year - agent.date_statut.year - ((today.month, today.day) < (agent.date_statut.month, agent.date_statut.day))
        else:
            delta = None
        donnees[i] = {
            'nom': agent.nom,
            'matricule': agent.matricule,
            'grade': agent.grade_actuel,
            'sexe': agent.sexe,
            'date_dispo': agent.date_statut.strftime('%d/%m/%Y') if agent.date_statut else "-",
            'duree': delta,
            'entite': agent.entite
        }

    html_string = render_to_string("personnel/liste_disponibilite_pdf.html", {
        'titre': "Liste des Agents en Disponibilité",
        'donnees': donnees
    })

    html = HTML(string=html_string)
    pdf_file = html.write_pdf()

    return HttpResponse(pdf_file, content_type='application/pdf')
    
def calcul_duree(depuis):
    if depuis:
        today = date.today()
        return today.year - depuis.year - ((today.month, today.day) < (depuis.month, depuis.day))
    return None

def format_duree(value):
    return f"{value} an{'s' if value > 1 else ''}" if value is not None else "-"

def liste_retraites_pdf(request):
    agents = Employe.objects.filter(statut='Mise à la retraite').order_by('nom')
    
    for emp in agents:
        # Calcule âge de départ et durée carrière si dates disponibles
        emp.age_depart = "-"
        emp.carriere = "-"
        
        if emp.date_naissance and emp.date_statut:
            age = date.today().year - emp.date_naissance.year - (
                (date.today().month, date.today().day) < (emp.date_naissance.month, emp.date_naissance.day)
            )
            emp.age_depart = f"{age} an" if age == 1 else f"{age} ans"

        if emp.date_engagement and emp.date_statut:
            duree = emp.date_statut.year - emp.date_engagement.year - (
                (emp.date_statut.month, emp.date_statut.day) < (emp.date_engagement.month, emp.date_engagement.day)
            )
            emp.carriere = f"{duree} an" if duree == 1 else f"{duree} ans"

    agents = list(enumerate(agents, start=1))  # ⬅ pour affichage avec numéros dans le template

    html_string = render_to_string("personnel/liste_retraites_pdf.html", {
        "agents": agents
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_retraites.pdf"

    # ✅ CSS complet avec centrage du titre
    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 {
            text-align: center;
            font-weight: bold;
            text-decoration: underline;
            margin-bottom: 10px;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }
        th {
            background-color: #f2f2f2;
            text-align: center;
            padding: 6px;
            border: 1px solid #000;
        }
        td {
            text-align: center;
            padding: 6px;
            border: 1px solid #000;
        }
        td.left {
            text-align: left;
        }
    ''')

    HTML(string=html_string).write_pdf(response, stylesheets=[css])
    return response


def liste_detachement_pdf(request):
    agents = Employe.objects.filter(statut='En détachement').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = "-"
        if emp.date_statut:
            duree = format_duree(calcul_duree(emp.date_statut))

        fonction = str(emp.fonction).strip() if emp.fonction else ''
        fonction = fonction if fonction.lower() != 'nan' and fonction != '' else '-'

        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            fonction,
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            duree,
            emp.entite or '-'
        ])

    html_string = render_to_string("personnel/liste_detachement_pdf.html", {
        "titre": "Liste des agents en détachement",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Fonction", "Date détachement", "Durée", "Entité"],
        "donnees": donnees
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_detachement.pdf"
    HTML(string=html_string).write_pdf(response, stylesheets=[CSS(string="@page { size: landscape; }")])
    return response


def liste_demissionnaires_pdf(request):
    agents = Employe.objects.filter(statut='Démission').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = "-"
        if emp.date_engagement and emp.date_statut:
            duree = format_duree(calcul_duree(emp.date_engagement))
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.date_engagement.strftime('%d/%m/%Y') if emp.date_engagement else '-',
            emp.date_statut.strftime('%d/%m/%Y') if emp.date_statut else '-',
            duree,
            emp.entite or '-'
        ])
    html_string = render_to_string("personnel/liste_demissionnaires_pdf.html", {
        "titre": "Liste des agents démissionnaires",
        "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Date engagement", "Date démission", "Carrière", "Entité"],
        "donnees": donnees
    })
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_demissionnaires.pdf"
    HTML(string=html_string).write_pdf(response, stylesheets=[CSS(string="@page { size: landscape; }")])
    return response

def liste_decedes_pdf(request):
    agents = Employe.objects.filter(statut="Décédé").order_by("nom")

    donnees = []
    for i, emp in enumerate(agents, start=1):
        donnees.append([
            i,
            emp.nom or "-",
            emp.matricule or "-",
            emp.sexe or "-",
            emp.date_naissance.strftime("%d/%m/%Y") if emp.date_naissance else "-",
            emp.date_statut.strftime("%d/%m/%Y") if emp.date_statut else "-",
            emp.entite or "-"
        ])

    html_string = render_to_string("personnel/liste_decedes_pdf.html", {
        "titre": "Liste des agents décédés",
        "colonnes": ["N°", "Nom", "Matricule", "Sexe", "Date de naissance", "Date décès", "Entité"],
        "donnees": donnees,
        "today": now()
    })

    css = CSS(string="""
        @page { size: A4 landscape; margin: 1cm; }
        h2 {
            text-align: center;
            font-weight: bold;
            text-decoration: underline;
        }
        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 12px;
            margin-top: 10px;
        }
        th {
            background-color: #f2f2f2;
            text-align: center;
        }
        td {
            text-align: center;
        }
        th, td {
            border: 1px solid #000;
            padding: 5px;
        }
        td.left {
            text-align: left;
        }
    """)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_decedes.pdf"
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response

def liste_demissionnaires_pdf(request):
    agents = Employe.objects.filter(statut='Démission').order_by('nom')

    for emp in agents:
        emp.carriere = "-"
        if emp.date_engagement and emp.date_statut:
            duree = emp.date_statut.year - emp.date_engagement.year - (
                (emp.date_statut.month, emp.date_statut.day) < (emp.date_engagement.month, emp.date_statut.day)
            )
            emp.carriere = f"{duree} an" if duree == 1 else f"{duree} ans"

    agents = list(enumerate(agents, start=1))
    
    html_string = render_to_string("personnel/liste_demissionnaires_pdf.html", {
        "agents": agents
    })

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_demissionnaires.pdf"
    css = CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    HTML(string=html_string).write_pdf(response, stylesheets=[css])
    return response
