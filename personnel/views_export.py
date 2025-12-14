# personnel/views_export.py
from datetime import date
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import render
from django.template.loader import render_to_string
from weasyprint import HTML, CSS

from .models import Employe


# -------------------------
# Helpers généraux
# -------------------------
def _calcul_age(date_naissance, ref=None):
    """Âge en années révolues ou None si absent."""
    if not date_naissance:
        return None
    ref = ref or date.today()
    years = ref.year - date_naissance.year - (
        (ref.month, ref.day) < (date_naissance.month, date_naissance.day)
    )
    return years


def _duree_depuis(start, ref=None):
    """Retour 'X an(s) Y mois' (lisible) ou '-' si start manquant."""
    if not start:
        return '-'
    ref = ref or date.today()
    y = ref.year - start.year - ((ref.month, ref.day) < (start.month, start.day))
    m = (ref.month - start.month - (1 if ref.day < start.day else 0)) % 12
    parts = []
    if y > 0:
        parts.append(f"{y} an{'s' if y > 1 else ''}")
    if m > 0:
        parts.append(f"{m} mois")
    return " ".join(parts) if parts else "0 mois"


def _prep_de(entite: str) -> str:
    """Préposition+article: 'de', 'de la', 'de l’', 'du'."""
    if not entite:
        return "de"
    e = entite.strip()
    if not e:
        return "de"
    voyelles = "AEIOUYHÀÂÄÉÈÊËÎÏÔÖÙÛÜ"
    head = e.split()[0].strip(".").capitalize()
    if e[0].upper() in voyelles:
        return "de l’"
    masculins = {"Bureau", "Centre", "Corps", "Secrétariat", "Collège", "CP"}
    feminins = {"Antenne", "Direction", "Dir", "DP", "Division"}
    if head in masculins:
        return "du"
    if head in feminins:
        return "de la"
    return "de"


def _titre_controleurs(entite: str | None, html=False) -> str:
    if not entite:
        txt = "Liste des Contrôleurs de la CNSS"
    else:
        prep = _prep_de(entite)
        sep = "" if prep.endswith("’") else " "
        txt = f"Liste des Contrôleurs {prep}{sep}{entite}"
    return f"<u>{txt}</u>" if html else txt


# -------------------------
# Ordre imposé des grades (Actifs)
# -------------------------
GRADE_ORDER_ACTIFS = [
    "Directeur",
    "Sous-Directeur",
    "Chef de Division",
    "Chef de Sce Ppal",
    "Chef de Service",
    "Chef de Sce Adjt",
    "Chef de Section",
    "Rédacteur Ppal",
    "Rédacteur",
    "Rédacteur Adjt",
    "Commis Chef",
    "Commis Ppal",
    "Commis",
    "Commis Adjt",
    "Agent Aux 1ère Cl",
    "Agent Aux 2è Cl",
    "Manœuvre Sp",
    "Manœuvre Lourd",
    "Manœuvre Ord",
]

# -------------------------
# Normalisation douce des labels de grade
# -------------------------
_NORMALIZE_MAP = {
    "chef de division": "Chef de Division",
    "chef de sce ppal": "Chef de Sce Ppal",
    "chef de service": "Chef de Service",
    "chef de sce adjt": "Chef de Sce Adjt",
    "chef de section": "Chef de Section",
    "redacteur ppal": "Rédacteur Ppal",
    "redacteur": "Rédacteur",
    "redacteur adjt": "Rédacteur Adjt",
    "commis chef": "Commis Chef",
    "commis ppal": "Commis Ppal",
    "commis": "Commis",
    "commis adjt": "Commis Adjt",
    "agent auxiliaire 1ere cl": "Agent Aux 1ère Cl",
    "agent auxiliaire 1ère cl": "Agent Aux 1ère Cl",
    "agent aux 1ere cl": "Agent Aux 1ère Cl",
    "agent aux 1ère cl": "Agent Aux 1ère Cl",
    "agent auxiliaire 2eme cl": "Agent Aux 2è Cl",
    "agent auxiliaire 2ème cl": "Agent Aux 2è Cl",
    "agent aux 2eme cl": "Agent Aux 2è Cl",
    "agent aux 2ème cl": "Agent Aux 2è Cl",
    "manoeuvre sp": "Manœuvre Sp",
    "manoeuvre lourd": "Manœuvre Lourd",
    "manoeuvre ord": "Manœuvre Ord",
}

def _normalize_grade(label: str | None) -> str | None:
    if not label:
        return label
    k = label.strip().lower()
    # équivalences de base pour variantes d'accents
    k = k.replace("é", "e").replace("œ", "oe")
    k = k.replace("1ère", "1ere").replace("1ere", "1ere")
    k = k.replace("2ème", "2eme").replace("2eme", "2eme")
    # map
    return _NORMALIZE_MAP.get(k, label.strip())


# -------------------------
# Vues “Total / Actifs” (compat templates : page_obj + agents + nb_total)
# -------------------------
@login_required(login_url='connexion')
def total_agents(request):
    qs = Employe.objects.all().order_by("nom", "prenom")
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "personnel/total_agents.html", {
        "title": "Total des agents",
        "page_obj": page_obj,               # si le template utilise une pagination
        "agents": page_obj.object_list,     # si le template itère sur "agents"
        "nb_total": paginator.count,        # utilisé par certains templates
    })


@login_required(login_url='connexion')
def agents_actifs(request):
    qs = Employe.objects.filter(statut__iexact="Actif").order_by("nom", "prenom")
    paginator = Paginator(qs, 50)
    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)
    return render(request, "personnel/total_agents.html", {
        "title": "Agents actifs",
        "page_obj": page_obj,
        "agents": page_obj.object_list,
        "nb_total": paginator.count,
    })


# -------------------------
# Listes diverses (HTML)
# -------------------------
@login_required(login_url='connexion')
def liste_actifs_par_entite(request):
    entite_choisie = request.GET.get('entite')
    toutes_les_entites = (
        Employe.objects.filter(statut='Actif')
        .values_list('entite', flat=True)
        .distinct()
    )

    if entite_choisie:
        agents = Employe.objects.filter(statut='Actif', entite=entite_choisie).order_by('nom')
        titre = f"Liste des Agents Actifs {_prep_de(entite_choisie)}{' ' if not _prep_de(entite_choisie).endswith('’') else ''}{entite_choisie}"
    else:
        agents = Employe.objects.filter(statut='Actif').order_by('nom')
        titre = "Liste des Agents Actifs par Entité"

    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = _duree_depuis(emp.date_affectation)
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

    colonnes = ['N°', 'Nom', 'Matricule', 'Sexe', 'Date engagement', 'Grade actuel',
                'Service', 'Fonction', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_actifs_par_entite.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': toutes_les_entites,
        'entite_choisie': entite_choisie
    })


@login_required(login_url='connexion')
def liste_decedes(request):
    agents = Employe.objects.filter(statut='Décédé').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        age_au_deces = "-"
        if emp.date_naissance and emp.date_statut:
            age = _calcul_age(emp.date_naissance, emp.date_statut)
            age_au_deces = f"{age} an{'s' if age and age > 1 else ''}" if age is not None else "-"
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Date naissance', 'Date décès', 'Âge au décès', 'Entité']
    return render(request, 'personnel/liste_decedes.html', {
        'titre': 'Liste des Agents Décédés',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
def liste_retraites(request):
    agents = Employe.objects.filter(statut__icontains='retraite').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        age_retraite = "-"
        duree_carriere = "-"
        if emp.date_naissance and emp.date_statut:
            age = _calcul_age(emp.date_naissance, emp.date_statut)
            age_retraite = f"{age} an{'s' if age and age > 1 else ''}" if age is not None else "-"
        if emp.date_engagement and emp.date_statut:
            duree = _calcul_age(emp.date_engagement, emp.date_statut)
            duree_carriere = f"{duree} an{'s' if duree and duree > 1 else ''}" if duree is not None else "-"
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Sexe', 'Date de naissance',
                'Date départ à la retraite', 'Âge départ', 'Date engagement', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_retraites.html', {
        'titre': 'Liste des Agents Retraités',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
def liste_demis(request):
    agents = Employe.objects.filter(statut__icontains='démission').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree_carriere = "-"
        if emp.date_engagement and emp.date_statut:
            duree = _calcul_age(emp.date_engagement, emp.date_statut)
            duree_carriere = f"{duree} an{'s' if duree and duree > 1 else ''}" if duree is not None else "-"
        else:
            duree = None
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Date engagement', 'Date démission', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_demis.html', {
        'titre': 'Liste des Agents Démissionnaires',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Date détachement', 'Entité']
    return render(request, 'personnel/liste_detaches.html', {
        'titre': 'Liste des Agents en Détachement',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
def liste_licencies(request):
    agents = Employe.objects.filter(statut__icontains='Licencié').order_by('nom')
    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree_carriere = "-"
        if emp.date_engagement and emp.date_statut:
            duree = _calcul_age(emp.date_engagement, emp.date_statut)
            duree_carriere = f"{duree} an{'s' if duree and duree > 1 else ''}" if duree is not None else "-"
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Date engagement', 'Date licenciement', 'Carrière', 'Entité']
    return render(request, 'personnel/liste_licencies.html', {
        'titre': 'Liste des Agents Licenciés',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
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
    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Date mise en disponibilité', 'Entité']
    return render(request, 'personnel/liste_disponibilites.html', {
        'titre': 'Liste des Agents en Disponibilité',
        'colonnes': colonnes,
        'donnees': donnees
    })


@login_required(login_url='connexion')
def liste_responsables_par_entite(request):
    entite_choisie = request.GET.get('entite')
    if entite_choisie:
        agents = Employe.objects.filter(fonction__icontains='responsable', entite=entite_choisie).order_by('nom')
        titre = f"Liste des Responsables du Service : {entite_choisie}"
    else:
        agents = Employe.objects.filter(fonction__icontains='responsable').order_by('nom')
        titre = "Liste des Responsables du Service"

    donnees = []
    for idx, emp in enumerate(agents, 1):
        duree = _duree_depuis(emp.date_affectation)
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
        'entite_choisie': entite_choisie
    })


# ---------- LISTE NIVEAU ÉTUDES / OPTION / ADRESSE (HTML) ----------
@login_required(login_url='connexion')
def liste_niveau_etudes_option_adresse(request):
    """
    Liste HTML des cadres et agents d'une entité choisie, triés :
      1) par ordre de grade (GRADE_ORDER_ACTIFS)
      2) par ordre alphabétique du nom à l'intérieur de chaque grade.

    Champs : N°, Nom, Matricule, Sexe, Grade actuel, Niveau études, Option, Adresse
    """
    entite_choisie = (request.GET.get("entite") or "").strip() or None

    # Base : on limite aux agents Actifs (adapter si tu veux inclure tous les statuts)
    qs_base = Employe.objects.filter(statut__iexact="Actif")

    # Liste des entités disponibles pour le filtre
    entites = (qs_base.exclude(entite__isnull=True)
                      .exclude(entite__exact="")
                      .values_list("entite", flat=True)
                      .distinct()
                      .order_by("entite"))

    qs = qs_base
    if entite_choisie:
        qs = qs.filter(entite=entite_choisie)

    agents = list(qs)

    # Préparation d'un index de rang pour les grades
    grade_rank = {g: i for i, g in enumerate(GRADE_ORDER_ACTIFS, start=1)}

    def sort_key(emp):
        grade_label = _normalize_grade(emp.grade_actuel)
        rang = grade_rank.get(grade_label, 999)
        nom = (emp.nom or "").upper()
        prenom = (emp.prenom or "").upper()
        return (rang, nom, prenom)

    agents_sorted = sorted(agents, key=sort_key)

    # Titre dynamique
    titre_base = "Niveau d'études, option et adresses des cadres et agents"
    if entite_choisie:
        prep = _prep_de(entite_choisie)
        sep = "" if prep.endswith("’") else " "
        titre = f"{titre_base} {prep}{sep}{entite_choisie}"
    else:
        titre = f"{titre_base} de la CNSS"

    colonnes = [
        "N°",
        "Nom",
        "Matricule",
        "Sexe",
        "Grade actuel",
        "Niveau études",
        "Option",
        "Adresse",
    ]

    donnees = []
    for idx, emp in enumerate(agents_sorted, start=1):
        nom_complet = f"{emp.nom or ''} {emp.prenom or ''}".strip() or "-"
        donnees.append([
            idx,
            nom_complet,
            emp.matricule or "-",
            emp.sexe or "-",
            _normalize_grade(emp.grade_actuel) or "-",
            getattr(emp, "niveau_etudes", None) or "-",
            getattr(emp, "option", None) or "-",
            getattr(emp, "adresse", None) or "-",
        ])

    # ✅ Contexte enrichi pour le template HTML
    context = {
        "titre": titre,
        "colonnes": colonnes,
        "donnees": donnees,
        "entites": entites,
        "entite_choisie": entite_choisie,
        # pour compatibilité avec le template existant
        "employes": agents_sorted,
        "entite": entite_choisie,
    }

    return render(request, "personnel/liste_niveau_etudes_option_adresse.html", context)


# ---------- LISTE ACTIFS FILTRÉE (HTML) ----------
@login_required(login_url='connexion')
def liste_actifs_filtre(request):
    """
    Liste HTML avec filtres par entité et grade actuel.
    - Uniquement statut = 'Actif'
    - Tri croissant par matricule
    - Titre : 'Tableau des agents actifs : [Entité] – [Grade]'
    Champs: N°, Nom (gauche), Matricule (centre), Fonction (gauche)
    """
    entite = (request.GET.get("entite") or "").strip()
    grade = (request.GET.get("grade") or "").strip()

    # Base: seulement les actifs
    qs = Employe.objects.filter(statut__iexact="Actif")
    if entite:
        qs = qs.filter(entite=entite)
    if grade:
        qs = qs.filter(grade_actuel=grade)

    qs = qs.order_by("matricule")

    # Récupération des CHOICES si disponibles
    try:
        from .models import ENTITE_CHOICES, GRADE_ACTUEL_CHOICES  # type: ignore
    except Exception:
        ENTITE_CHOICES, GRADE_ACTUEL_CHOICES = None, None

    def _label_from_choices(value, choices):
        if not value or not choices:
            return value or None
        try:
            return dict(choices).get(value, value)
        except Exception:
            return value

    entite_label = _label_from_choices(entite, ENTITE_CHOICES) if ENTITE_CHOICES else (entite or None)
    grade_label = _label_from_choices(grade, GRADE_ACTUEL_CHOICES) if GRADE_ACTUEL_CHOICES else (grade or None)

    titre = f"Tableau des agents actifs : {entite_label or 'Toutes entités'} – {grade_label or 'Tous grades'}"

    # Options des <select>
    if ENTITE_CHOICES:
        entites = [("", "— Toutes —")] + list(ENTITE_CHOICES)
    else:
        entites = [("", "— Toutes —")] + [
            (e, e) for e in (Employe.objects
                             .filter(statut__iexact="Actif")
                             .exclude(entite__isnull=True).exclude(entite__exact="")
                             .values_list("entite", flat=True).distinct().order_by("entite"))
        ]

    if GRADE_ACTUEL_CHOICES:
        grades = [("", "— Tous —")] + list(GRADE_ACTUEL_CHOICES)
    else:
        grades = [("", "— Tous —")] + [
            (g, g) for g in (Employe.objects
                             .filter(statut__iexact="Actif")
                             .exclude(grade_actuel__isnull=True).exclude(grade_actuel__exact="")
                             .values_list("grade_actuel", flat=True).distinct().order_by("grade_actuel"))
        ]

    context = {
        "titre": titre,
        "agents": qs,
        "entites": entites,
        "grades": grades,
        "entite_sel": entite,
        "grade_sel": grade,
    }
    return render(request, "personnel/liste_actifs_filtre.html", context)


# ---------- LISTE CONTRÔLEURS (HTML) ----------
@login_required(login_url='connexion')
def liste_controleurs(request):
    entite_choisie = (request.GET.get('entite') or "").strip() or None

    filtre_controle = (
        Q(service__icontains='Contrôle') |
        Q(service__icontains='Controle') |
        Q(fonction__icontains='Contrôleur') |
        Q(fonction__icontains='Controleur')
    )
    qs_base = Employe.objects.filter(filtre_controle)

    entites = (qs_base.exclude(entite__isnull=True)
                      .exclude(entite__exact='')
                      .values_list('entite', flat=True)
                      .distinct()
                      .order_by('entite'))

    qs = qs_base
    if entite_choisie:
        qs = qs.filter(Q(entite__iexact=entite_choisie) | Q(entite__icontains=entite_choisie))
        titre = _titre_controleurs(entite_choisie, html=False)
    else:
        titre = _titre_controleurs(None, html=False)

    agents = qs.order_by('entite', 'nom', 'prenom')

    donnees = []
    for idx, emp in enumerate(agents, 1):
        age = _calcul_age(emp.date_naissance)  # nombre ou None
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            emp.fonction or '-',
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            (age if age is not None else '-'),  # item.7
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            _duree_depuis(emp.date_affectation),
            emp.entite or '-'
        ])

    colonnes = ['N°', 'Nom', 'Matricule', 'Grade actuel', 'Sexe',
                'Fonction', 'Date naissance', 'Âge', 'Date affectation', 'Durée affectation', 'Entité']

    return render(request, 'personnel/liste_controleurs.html', {
        'titre': titre,
        'colonnes': colonnes,
        'donnees': donnees,
        'entites': entites,
        'selected_entite': entite_choisie,
        'entite_choisie': entite_choisie,
    })


# ---------- LISTE CONTRÔLEURS (PDF) ----------
@login_required(login_url='connexion')
def liste_controleurs_pdf(request):
    entite_choisie = (request.GET.get('entite') or "").strip() or None

    filtre_controle = (
        Q(service__icontains='Contrôle') |
        Q(service__icontains='Controle') |
        Q(fonction__icontains='Contrôleur') |
        Q(fonction__icontains='Controleur')
    )
    qs = Employe.objects.filter(filtre_controle)
    if entite_choisie:
        qs = qs.filter(Q(entite__iexact=entite_choisie) | Q(entite__icontains=entite_choisie))

    agents = qs.order_by('entite', 'nom', 'prenom')

    donnees = []
    for idx, emp in enumerate(agents, 1):
        age = _calcul_age(emp.date_naissance)
        age_display = "-" if age is None else (f"{age} an" if age == 1 else f"{age} ans")
        css_class = "highlight-age" if (isinstance(age, int) and age >= 55) else ""
        donnees.append([
            idx,  # 0
            emp.nom or '-',  # 1
            emp.matricule or '-',  # 2
            emp.grade_actuel or '-',  # 3
            emp.sexe or '-',  # 4
            emp.fonction or '-',  # 5
            emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',  # 6
            age_display,  # 7
            emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',  # 8
            _duree_depuis(emp.date_affectation),  # 9
            emp.entite or '-',  # 10
            css_class,  # 11 (surbrillance)
        ])

    titre = _titre_controleurs(entite_choisie, html=True)

    html_string = render_to_string('personnel/liste_controleurs_pdf.html', {
        'donnees': donnees,
        'titre': titre,
        'selected_entite': entite_choisie,
    })

    response = HttpResponse(content_type='application/pdf')
    safe_entite = (entite_choisie or "tous").replace(" ", "_")
    response['Content-Disposition'] = f'inline; filename=controleurs_{safe_entite}.pdf'

    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { border: 1px solid #aaa; padding: 6px; text-align: center; }
        th { background: #f0f0f0; }
        td.left, th.left { text-align: left; }

        /* Surbrillance 55 ans+ (tolérante aux variantes) */
        tr.highlight-age > td,
        td.highlight-age,
        tr.True > td, td.True,
        tr.true > td, td.true {
            background-color: #d0e7ff !important;
        }
    ''')

    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


# --------- Effectif par entité (HTML) ---------
@login_required(login_url='connexion')
def liste_effectif_par_entite(request):
    effectifs = (
        Employe.objects.values('entite')
        .annotate(total=Count('id'))
        .order_by('entite')
    )
    total_general = sum(item['total'] for item in effectifs)

    donnees = []
    for i, item in enumerate(effectifs, start=1):
        donnees.append({
            'numero': i,
            'entite': item['entite'] or "-",
            'effectif': item['total']
        })
    return render(request, 'personnel/liste_effectif_par_entite.html', {
        'donnees': donnees,
        'total_general': total_general
    })


# --------- Effectif Actifs par grade (HTML) ---------
@login_required(login_url='connexion')
def effectif_actifs_par_grade(request):
    """
    Tableau synthétique : Effectif par grade pour les seuls agents 'Actif',
    trié suivant GRADE_ORDER_ACTIFS, avec total général.
    """
    # Comptage DB : { grade_actuel -> total }
    data_qs = (
        Employe.objects.filter(statut__iexact="Actif")
        .values("grade_actuel")
        .annotate(total=Count("id"))
    )
    counts = {row["grade_actuel"]: row["total"] for row in data_qs}

    # Fournit 'donnees' pour compat, et 'rows' en alias
    donnees = []
    total_general = 0
    for i, grade in enumerate(GRADE_ORDER_ACTIFS, start=1):
        n = counts.get(grade, 0)
        donnees.append({"numero": i, "grade": grade, "effectif": n})
        total_general += n

    ctx = {
        "titre": "Effectif des agents actifs par grade",
        "donnees": donnees,          # <- attendu par certains templates
        "rows": donnees,             # <- alias si d'autres templates utilisaient 'rows'
        "total_general": total_general,
    }
    return render(request, "personnel/effectif_actifs_par_grade.html", ctx)


# --------- Effectif Actifs par grade (PDF) ---------
@login_required(login_url='connexion')
def effectif_actifs_par_grade_pdf(request):
    """
    Version PDF du tableau Effectif Actifs par grade.
    """
    data_qs = (
        Employe.objects.filter(statut__iexact="Actif")
        .values("grade_actuel")
        .annotate(total=Count("id"))
    )
    counts = {row["grade_actuel"]: row["total"] for row in data_qs}

    rows = []
    total_general = 0
    for i, grade in enumerate(GRADE_ORDER_ACTIFS, start=1):
        n = counts.get(grade, 0)
        rows.append({"rang": i, "grade": grade, "total": n})
        total_general += n

    html_string = render_to_string(
        "personnel/effectif_actifs_par_grade_pdf.html",
        {
            "titre": "Effectif des agents actifs par grade",
            "rows": rows,
            "total_general": total_general,
        },
    )

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="effectif_actifs_par_grade.pdf"'

    css = CSS(string='''
        @page { size: A4 landscape; margin: 14mm; }
        body { font-family: Arial, sans-serif; font-size: 12px; color:#111; }
        h1 { text-align:center; text-decoration: underline; margin: 0 0 8px 0; }
        table { width:100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; }
        th, td { border:1px solid #999; padding:6px; }
        th { text-align:center; background:#eee; }
        td.num { text-align:center; }
        tfoot td { font-weight:bold; }
    ''')

    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[css])
    return response


# -------------------------
# Exports Excel (ROBUSTES)
# -------------------------

def _df_to_xlsx_response(df, filename: str, sheet_name: str = "Employés"):
    """Écrit un DataFrame dans un fichier .xlsx en mémoire et renvoie la réponse HTTP.
       Fallback CSV si pandas/openpyxl sont absents.
    """
    try:
        import pandas as pd  # import local (pour être tolérant si indisponible)
        buf = BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            df.to_excel(writer, index=False, sheet_name=sheet_name)
        data = buf.getvalue()
        resp = HttpResponse(
            data,
            content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
        resp["Content-Disposition"] = f'attachment; filename="{filename}"'
        resp["Content-Length"] = str(len(data))
        return resp
    except ModuleNotFoundError:
        # Fallback CSV si pandas/openpyxl indisponibles
        import csv
        import io as _io
        if hasattr(df, "to_dict"):
            rows = df.to_dict(orient="records")
        else:
            rows = list(df)
        fieldnames = list(rows[0].keys()) if rows else []
        text_buf = _io.StringIO()
        writer = csv.DictWriter(text_buf, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
        csv_bytes = text_buf.getvalue().encode("utf-8-sig")
        resp = HttpResponse(csv_bytes, content_type="text/csv; charset=utf-8")
        resp["Content-Disposition"] = f'attachment; filename="{filename.replace(".xlsx", ".csv")}"'
        resp["Content-Length"] = str(len(csv_bytes))
        return resp


@login_required(login_url='connexion')
def export_employes_excel_complet(request):
    # Accès réservé aux superutilisateurs, cohérent avec l’affichage du bouton dans le template
    if not getattr(request.user, "is_superuser", False):
        return HttpResponse("Accès réservé aux administrateurs.", status=403)
    import pandas as pd
    employes = list(Employe.objects.all().values())
    df = pd.DataFrame(employes).fillna("-")
    return _df_to_xlsx_response(df, filename="liste_employes_complete.xlsx", sheet_name="Employés")


@login_required(login_url='connexion')
def export_employes_excel(request):
    import pandas as pd
    cols = [
        "nom", "prenom", "matricule", "grade_actuel",
        "sexe", "service", "fonction", "statut", "entite",
    ]
    employes = list(Employe.objects.all().values(*cols))
    df = pd.DataFrame(employes, columns=cols).fillna("-")
    return _df_to_xlsx_response(df, filename="liste_employes.xlsx", sheet_name="Employés")
