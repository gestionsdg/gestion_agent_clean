# personnel/views_pdf_weasyprint.py
from datetime import date
from collections import defaultdict
import base64
import mimetypes  # ✅ pour détecter le bon MIME de la photo
import re        # ✅ pour ajuster le titre dans le HTML rendu

from django.contrib.auth.decorators import login_required
from django.contrib.staticfiles import finders
from django.db.models import Q, Count
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render  # ✅ render ajouté
from django.template.loader import render_to_string
from django.template import TemplateDoesNotExist
from django.utils.dateformat import DateFormat
from django.utils.timezone import now
from django.utils import timezone  # ✅ pour localdate()

from weasyprint import HTML, CSS
from dateutil.relativedelta import relativedelta  # ✅ pour +65 ans

from .models import Employe

# ---- Imports utilitaires robustes (fallback si utils indisponible) ----
try:
    from .utils import calcul_duree_detaillee, format_duree
except Exception:
    # Fallbacks très simples pour éviter un 500 si utils.py manque
    def calcul_duree_detaillee(d1, d2=None):
        if not d1:
            return {"years": 0, "months": 0}
        ref = d2 or date.today()
        y = ref.year - d1.year - ((ref.month, ref.day) < (d1.month, d1.day))
        m = (ref.month - d1.month - (1 if ref.day < d1.day else 0)) % 12
        return {"years": max(0, y), "months": max(0, m)}

    def format_duree(dd):
        y, m = dd.get("years", 0), dd.get("months", 0)
        parts = []
        if y:
            parts.append(f"{y} an{'s' if y > 1 else ''}")
        if m:
            parts.append(f"{m} mois")
        return " ".join(parts) if parts else "0 mois"


# ---------- Helpers & constantes ----------
ORDRE_FONCTIONS_CONTROLE = [
    "Coordonnateur",
    "Coordonnateur a.i",
    "Coordonnateur Adjoint",
    "Coordonnateur Adjoint Technique",
    "Coordonnateur Adjoint Administratif",
    "Coordonnateur Adjoint Contentieux",
    "Contrôleur",
]

# Hiérarchie de direction (noms longs)
ORDRE_FONCTIONS_DG = [
    "Assistant Principal/DG",
    "Directeur",
    "Directeur a.i",
    "Directeur Urbain",
    "Directeur Provincial",
    "Directeur Sans Fonction",
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
    "Sous-Directeur Comptable",
    "Sous-Directeur Budget",
    "Sous-Directeur Log. et Maint.",
    "Sous-Directeur des Appro",
    "Sous-Directeur Juridique",
    "Sous-Directeur Contentieux",
    "Sous-Directeur de Grandes Entreprises",
    "Sous-Directeur des Statistiques",
    "Sous-Directeur des Etudes",
    "Sous-Directeur Action Sociale",
    "Sous-Directeur Pharmacie et Labo",
    "Sous-Directeur Technique",
    "Sous-Directeur des Baux et Loyers",
    "Sous-Directeur Adm. et Fin.",
    "Sous-Directeur des Actions Sanitaires",
    "Sous-Directeur",
]

ORDRE_GRADES = [
    "Directeur", "Sous-Directeur", "Chef de Division", "Chef de Sce Ppal",
    "Chef de Service", "Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal",
    "Rédacteur", "Rédacteur Adjt", "Commis Chef", "Commis Ppal", "Commis",
    "Commis Adjt", "Agent Aux 1ère Cl", "Agent Aux 2è Cl", "Manœuvre Sp",
    "Manœuvre Lourd", "Manœuvre Ord",
]

# ✅ Préposition/Article pour le titre (de / de la / de l'/ du)
def _prep_de(entite: str) -> str:
    """
    Préposition+article: 'de', 'de la', 'de l’', 'du' selon l'entité.
    Copié de views_export.py pour cohérence des titres.
    """
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


# ✅ Retraite & élagage
RETIREMENT_AGE = 65
EXCLUSION_AGE = 66  # élaguer tout agent ayant 66 ans au cours de l'année en cours


def _logo_b64(static_path="images/logo_cnss.png"):
    """
    Retourne une data-URL base64 pour un fichier statique, ou None si introuvable.
    static_path : chemin RELATIF à /static/, ex: "images/logo_cnss.png"
    """
    path = finders.find(static_path)
    if not path:
        return None
    with open(path, "rb") as f:
        data = f.read()
    mime, _ = mimetypes.guess_type(static_path)
    if not mime:
        mime = "image/png"
    return f"data:{mime};base64," + base64.b64encode(data).decode("ascii")


def _fieldfile_to_b64(fieldfile):
    """
    Convertit un FileField/ImageField en data URL base64, ou None si indisponible.
    Utile pour WeasyPrint en prod (pas d'accès direct à /media/).
    """
    if not fieldfile:
        return None
    try:
        f = fieldfile.open("rb")
        try:
            data = f.read()
        finally:
            try:
                f.close()
            except Exception:
                pass
    except Exception:
        return None

    name = getattr(fieldfile, "name", "") or ""
    mime, _ = mimetypes.guess_type(name)
    if not mime:
        mime = "image/jpeg"
    return "data:%s;base64,%s" % (mime, base64.b64encode(data).decode("ascii"))


def _fonction_priority(lst, fonction):
    try:
        return lst.index(fonction)
    except ValueError:
        return len(lst)


def calcul_age(date_naissance):
    if not date_naissance:
        return None
    today = date.today()
    return today.year - date_naissance.year - (
        (today.month, today.day) < (date_naissance.month, date_naissance.day)
    )


def nettoyer_unite_ans(texte):
    """
    Supprime les doublons 'ans ans' ou 'an ans' dans les chaînes générées par format_duree().
    """
    if not texte:
        return "-"
    return (
        texte.replace(" ans ans", " ans")
        .replace(" an ans", " an")
        .replace(" an an", " an")
    )


def _get_year(request):
    """
    Récupère ?year=AAAA si valide, sinon None.
    """
    raw = (request.GET.get("year") or "").strip()
    if raw.isdigit() and len(raw) == 4:
        y = int(raw)
        if 1900 <= y <= 2100:
            return y
    return None


def _label_from_choices(value, choices):
    """Retourne le libellé humain d'une valeur issue d'un CHOICES (si dispo)."""
    if not value or not choices:
        return None
    try:
        d = dict(choices)
        return d.get(value, value)
    except Exception:
        return value


# ✅ Helpers retraite
def _age_aujourdhui(dnaiss: date, today: date) -> int | None:
    if not dnaiss:
        return None
    return today.year - dnaiss.year - ((today.month, today.day) < (dnaiss.month, dnaiss.day))


def _categorie_retraite(dnaiss: date, current_year: int) -> str | None:
    """
    Catégorie selon l'année des 65 ans par rapport à l'année courante.
      -> 'annee_en_cours', 'dans_1_an', 'dans_2_ans', 'dans_3_ans', 'dans_4_ans', 'dans_5_ans'
      -> None si hors périmètre
    """
    if not dnaiss:
        return None
    year_65 = dnaiss.year + RETIREMENT_AGE
    delta = year_65 - current_year
    if delta == 0:
        return "annee_en_cours"
    elif delta == 1:
        return "dans_1_an"
    elif delta == 2:
        return "dans_2_ans"
    elif delta == 3:
        return "dans_3_ans"
    elif delta == 4:
        return "dans_4_ans"
    elif delta == 5:
        return "dans_5_ans"
    return None


def _date_depart_retraite(dnaiss: date) -> date | None:
    """Retourne la date de départ en retraite (65 ans) à partir de la date de naissance."""
    if not dnaiss:
        return None
    return dnaiss + relativedelta(years=RETIREMENT_AGE)


# ---------- Fallback PDF minimal si un template est introuvable ----------
def _pdf_fallback(title: str, table_rows, columns=None):
    """
    Construit un PDF minimal (via HTML inline) si le template attendu n'existe pas.
    table_rows: liste de listes ou de dicts (valeurs rendues en <td>)
    columns: entêtes facultatives
    """
    if not columns and table_rows:
        # colonnes génériques
        ncols = len(table_rows[0]) if isinstance(table_rows[0], (list, tuple)) else len(table_rows[0].keys())
        columns = [f"Col {i+1}" for i in range(ncols)]
    thead = "".join(f"<th>{c}</th>" for c in (columns or []))
    body = []
    for row in table_rows:
        if isinstance(row, dict):
            vals = row.values()
        else:
            vals = row
        body.append("<tr>" + "".join(f"<td>{(v if v is not None else '-')}</td>" for v in vals) + "</tr>")
    html = f"""
    <html><head><meta charset="utf-8"><title>{title}</title>
    <style>
      @page {{ size: A4 landscape; margin: 12mm; }}
      table {{ width:100%; border-collapse:collapse; font-size:12px; }}
      th,td {{ border:1px solid #000; padding:6px; text-align:center; }}
      th {{ background:#eee; }}
      h2 {{ text-align:center; text-decoration:underline; margin:0 0 8px 0; }}
    </style></head>
    <body>
      <h2>{title}</h2>
      <table>
        <thead><tr>{thead}</tr></thead>
        <tbody>{"".join(body)}</tbody>
      </table>
    </body></html>
    """
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="fallback.pdf"'
    HTML(string=html).write_pdf(response)
    return response


# ---------- Vues PDF ----------
@login_required(login_url='connexion')
def fiche_employe_pdf(request, pk):
    employe = get_object_or_404(Employe, pk=pk)
    photo_url_for_pdf = _fieldfile_to_b64(getattr(employe, "photo", None))

    context = {
        "employe": employe,
        "age": format_duree(calcul_duree_detaillee(employe.date_naissance)),
        "anciennete_societe": format_duree(calcul_duree_detaillee(employe.date_engagement)),
        "anciennete_grade": format_duree(calcul_duree_detaillee(employe.date_derniere_promotion)),
        "duree_affectation": format_duree(calcul_duree_detaillee(employe.date_affectation)),
        "duree_prise_fonction": format_duree(calcul_duree_detaillee(employe.date_prise_fonction)),
        "date_impression": DateFormat(date.today()).format("d/m/Y"),
        "logo_b64": _logo_b64("images/logo_cnss.png"),
        "photo_url_for_pdf": photo_url_for_pdf,
        "is_pdf": True,
    }

    try:
        html_string = render_to_string("personnel/fiche_employe.html", context)
    except TemplateDoesNotExist:
        # Fallback: tableau simple avec quelques infos clés
        rows = [[
            employe.nom or "-", employe.prenom or "-", employe.matricule or "-",
            employe.grade_actuel or "-", employe.entite or "-"
        ]]
        return _pdf_fallback("Fiche Employé", rows, ["Nom", "Prénom", "Matricule", "Grade", "Entité"])

    response = HttpResponse(content_type="application/pdf")
    filename = f'fiche_{(employe.matricule or "employe")}.pdf'
    response["Content-Disposition"] = f'inline; filename="{filename}"'
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(response)
    return response


@login_required(login_url='connexion')
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
            duree = format_duree(calcul_duree_detaillee(emp.date_affectation))

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

    try:
        html_string = render_to_string('personnel/liste_responsables_pdf.html', {
            'donnees': donnees,
            'titre': titre,
            'logo_b64': _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        return _pdf_fallback(titre, donnees, ["N°","Nom","Matricule","Grade","Service","Date affectation","Durée","Entité"])

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=responsables_{entite or "tous"}.pdf'
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response)
    return response


@login_required(login_url='connexion')
def liste_controleurs_pdf(request):
    entite_raw = (request.GET.get('entite') or '').strip()
    bad_values = {'', 'toutes', 'toutes entites', 'toutes entités', 'all', 'tous'}
    entite = '' if entite_raw.lower() in bad_values else entite_raw

    qs = Employe.objects.filter(
        Q(fonction__icontains='contrôleur') |
        Q(fonction__icontains='controleur') |
        Q(service__icontains='contrôle')  |
        Q(service__icontains='controle')
    )
    if entite:
        qs = qs.filter(entite__iexact=entite)

    ordre_fonctions_loc = [
        "Coordonnateur",
        "Coordonnateur a.i",
        "Coordonnateur Adjoint",
        "Coordonnateur Adjoint Technique",
        "Coordonnateur Adjoint Technique a.i",
        "Coordonnateur Adjoint Administratif",
        "Coordonnateur Adjoint Administratif a.i",
        "Contrôleur",
    ]
    ordre_grades = [
        "Chef de Division", "Chef de Sce Ppal", "Chef de Service", "Chef de Sce Adjt",
        "Chef de Section", "Rédacteur Ppal", "Rédacteur", "Rédacteur Adjt",
    ]

    def classement(emp):
        f_idx = _fonction_priority(ordre_fonctions_loc, emp.fonction)
        g_idx = _fonction_priority(ordre_grades, emp.grade_actuel)
        return (f_idx, g_idx, (emp.nom or '').lower())

    agents = sorted(qs, key=classement)

    donnees = []
    for idx, emp in enumerate(agents, 1):
        age_int = calcul_age(emp.date_naissance)
        age_str = "-" if age_int is None else (f"{age_int} an" if age_int == 1 else f"{age_int} ans")
        duree_aff = format_duree(calcul_duree_detaillee(emp.date_affectation))

        donnees.append({
            "numero": idx,
            "nom": emp.nom or '-',
            "matricule": emp.matricule or '-',
            "grade": emp.grade_actuel or '-',
            "sexe": emp.sexe or '-',
            "fonction": emp.fonction or '-',
            "date_naissance": emp.date_naissance.strftime('%d/%m/%Y') if emp.date_naissance else '-',
            "age": age_str,
            # ✅ correction de la coquille dans strftime :
            "date_affectation": emp.date_affectation.strftime('%d/%m/%Y') if emp.date_affectation else '-',
            "duree_affectation": duree_aff or '-',
            "entite": emp.entite or '-',
            "senior": (age_int is not None and age_int >= 55),
        })

    titre = f"Liste des contrôleurs : {entite}" if entite else "Liste des contrôleurs de la CNSS"

    try:
        html_string = render_to_string('personnel/liste_controleurs_pdf.html', {
            'donnees': donnees,
            'titre': titre,
            'logo_b64': _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        # transformer donnees (dicts) en lignes
        rows = [[d["numero"], d["nom"], d["matricule"], d["grade"], d["sexe"], d["fonction"],
                 d["date_naissance"], d["age"], d["date_affectation"], d["duree_affectation"], d["entite"]] for d in donnees]
        cols = ["N°","Nom","Matricule","Grade","Sexe","Fonction","Naissance","Âge","Date affect.","Durée","Entité"]
        return _pdf_fallback(titre, rows, cols)

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename=controleurs_{entite or "tous"}.pdf'
    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; }
        th, td { border: 1px solid black; padding: 5px; text-align: center; }
        th.left, td.left { text-align: left; }
        tr.senior { background-color: #e6f2ff; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


@login_required(login_url='connexion')
def liste_responsables_coordonnateurs_pdf(request):
    entite_raw = (request.GET.get('entite') or request.POST.get('entite') or '').strip()
    bad_values = {'', 'toutes', 'toutes entites', 'toutes entités', 'all'}
    entite = '' if entite_raw.lower() in bad_values else entite_raw

    base_qs = Employe.objects.filter(
        fonction__in(["Responsable", "Responsable a.i", "Coordonnateur", "Coordonnateur a.i"])
    )
    agents = base_qs.filter(entite__iexact=entite) if entite else base_qs
    titre_suffix = entite if entite else "Toutes Entités"

    agents = sorted(
        agents,
        key=lambda x: (
            _fonction_priority(ORDRE_GRADES, x.grade_actuel),
            x.nom or ""
        )
    )

    donnees = []
    for i, agent in enumerate(agents, start=1):
        donnees.append([
            i,
            agent.nom or "",
            agent.matricule or "",
            agent.grade_actuel or "",
            agent.sexe or "",
            agent.service or "",
            agent.fonction or "",
            agent.date_affectation.strftime("%d/%m/%Y") if agent.date_affectation else "-",
            format_duree(calcul_duree_detaillee(agent.date_affectation)),
        ])

    try:
        html_string = render_to_string(
            "personnel/liste_responsables_coordonnateurs_pdf.html",
            {
                "titre": f"Liste des Responsables de Service - {titre_suffix}",
                "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Service", "Fonction", "Date affectation", "Durée affectation"],
                "donnees": donnees,
                "entite": entite,
                "today": now(),
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            },
        )
    except TemplateDoesNotExist:
        return _pdf_fallback(f"Liste des Responsables de Service - {titre_suffix}", donnees)

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


@login_required(login_url='connexion')
def liste_actifs_par_entite_pdf(request):
    entite = request.GET.get('entite', '').strip()
    agents = Employe.objects.filter(entite=entite, statut="Actif").order_by('nom') if entite else []

    groupes_services = defaultdict(lambda: {'cadres': [], 'agents': []})
    for emp in agents:
        service = emp.service or "Non défini"
        if emp.grade_actuel in ["Directeur", "Sous-Directeur"]:
            groupes_services[service]['cadres'].append(emp)
        else:
            groupes_services[service]['agents'].append(emp)

    donnees_groupes = []

    # Cadres
    for service, groupes in sorted(groupes_services.items()):
        cadres = sorted(
            groupes['cadres'],
            key=lambda x: (
                _fonction_priority(ORDRE_GRADES, x.grade_actuel),
                x.nom or ""
            )
        )
        lignes_cadres = []
        for i, emp in enumerate(cadres, 1):
            lignes_cadres.append([
                i,
                emp.nom or "-",
                emp.matricule or "-",
                emp.sexe or "-",
                emp.grade_actuel or "-",
                emp.fonction or "-",
                emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
                format_duree(calcul_duree_detaillee(emp.date_affectation)),
            ])

        # Agents
        ordre_fonctions_prioritaires = [
            "Responsable", "Responsable a.i",
            "Coordonnateur", "Coordonnateur a.i",
            "Coordonnateur Adjoint",
            "Coordonnateur Adjoint Technique", "Coordonnateur Adjoint Technique a.i",
            "Coordonnateur Adjoint Administratif", "Coordonnateur Adjoint Administratif a.i",
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
                _fonction_priority(ORDRE_GRADES, x.grade_actuel),
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
                format_duree(calcul_duree_detaillee(emp.date_affectation)),
            ])

        donnees_groupes.append((service, lignes_cadres, lignes_agents))

    try:
        html_string = render_to_string("personnel/liste_actifs_par_entite_pdf.html", {
            "titre": f"Liste des agents actifs : {entite}" if entite else "Liste des agents actifs",
            "entite": entite,
            "colonnes": ["N°", "Nom", "Matricule", "Sexe", "Grade actuel", "Fonction", "Date affectation", "Durée affectation"],
            "donnees_groupes": donnees_groupes,
            "today": now(),
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        # Fallback: aplat simple agents
        flat = []
        for _, lc, la in donnees_groupes:
            flat += lc + la
        return _pdf_fallback("Liste des agents actifs", flat)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = f"inline; filename=actifs_{entite or 'tous'}.pdf"
    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; font-size: 16px; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 5px; }
        th, td { border: 1px solid black; padding: 5px; }
        th { background-color: #eee; text-align: center; }
        td:nth-child(1), td:nth-child(3), td:nth-child(4), td:nth-child(8) { text-align: center; }
        td:nth-child(2), td:nth-child(5), td:nth-child(6), td:nth-child(7) { text-align: left; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


# ---------- ✅ NOUVELLE LISTE PDF : Niveau études / Option / Adresse ----------
@login_required(login_url='connexion')
def liste_niveau_etudes_option_adresse_pdf(request):
    """
    Liste PDF des cadres et agents, triés :
      1) par ordre de grade (ORDRE_GRADES)
      2) par ordre alphabétique du nom à l'intérieur de chaque grade.

    Champs affichés (définitif) :
      N°, Nom, Matricule, Sexe, Grade actuel,
      Niveau d'études, Option, Adresse

    ✅ La colonne Entité est SUPPRIMÉE du tableau :
       - l'information d'entité est uniquement dans le titre.
    """
    entite_choisie = (request.GET.get("entite") or "").strip()
    option_choisie = (request.GET.get("option") or "").strip()

    # Base : seulement les Actifs (comme la vue HTML)
    qs = Employe.objects.filter(statut__iexact="Actif")

    if entite_choisie:
        qs = qs.filter(entite=entite_choisie)

    # Filtrage éventuel par option
    if option_choisie:
        qs = qs.filter(option__iexact=option_choisie)

    agents = list(qs)

    # Tri : ordre de grade + nom/prénom
    def sort_key(emp):
        grade_label = _normalize_grade(emp.grade_actuel)
        rang = grade_priority(grade_label)
        nom = (emp.nom or "").upper()
        prenom = (emp.prenom or "").upper()
        return (rang, nom, prenom)

    agents_sorted = sorted(agents, key=sort_key)

    # Titre dynamique (entité mise uniquement ici)
    titre_base = "Niveau d'études, option et adresses des cadres et agents"

    if entite_choisie:
        prep = _prep_de(entite_choisie)
        sep = "" if prep.endswith("’") else " "
        suffix_entite = f"{prep}{sep}{entite_choisie}"
    else:
        suffix_entite = "de la CNSS"

    if option_choisie:
        titre = f"{titre_base} {suffix_entite} – Option : {option_choisie}"
    else:
        titre = f"{titre_base} {suffix_entite}"

    # ✅ Colonnes définitives : SANS ENTITÉ, AVEC OPTION
    colonnes = [
        "N°",
        "Nom",
        "Matricule",
        "Sexe",
        "Grade actuel",
        "Niveau d'études",
        "Option",
        "Adresse",
    ]

    donnees = []
    for idx, emp in enumerate(agents_sorted, start=1):
        nom_complet = f"{emp.nom or ''} {emp.prenom or ''}".strip() or "-"
        donnees.append([
            idx,                                         # N°
            nom_complet,                                # Nom
            emp.matricule or "-",                       # Matricule
            emp.sexe or "-",                            # Sexe
            _normalize_grade(emp.grade_actuel) or "-",  # Grade actuel
            getattr(emp, "niveau_etudes", None) or "-", # Niveau d'études
            getattr(emp, "option", None) or "-",        # Option
            getattr(emp, "adresse", None) or "-",       # Adresse
        ])

    try:
        html_string = render_to_string(
            "personnel/liste_niveau_etudes_option_adresse_pdf.html",
            {
                "titre": titre,
                "colonnes": colonnes,
                "donnees": donnees,
                "today": now(),
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            },
        )
    except TemplateDoesNotExist:
        # Fallback simple : mêmes colonnes (sans entité)
        return _pdf_fallback(titre, donnees, colonnes)

    response = HttpResponse(content_type="application/pdf")
    safe_entite = (entite_choisie or "CNSS").replace(" ", "_")
    response["Content-Disposition"] = (
        f'inline; filename="niveau_etudes_option_adresse_{safe_entite}.pdf"'
    )

    css = CSS(string="""
        @page {
            size: A4 landscape;
            margin: 1cm;
        }

        h2 {
            text-align: center;
            font-weight: bold;
            text-decoration: underline;
            margin-bottom: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 10px;
        }

        th, td {
            border: 0.5pt solid #555;
            padding: 3px 4px;
        }

        th {
            background-color: #f2f2f2;
            text-align: center;
        }

        /* Alignements colonnes */
        td:nth-child(1),
        td:nth-child(3),
        td:nth-child(4) {
            text-align: center;
        }

        td:nth-child(2),
        td:nth-child(5),
        td:nth-child(6),
        td:nth-child(7),
        td:nth-child(8) {
            text-align: left;
        }
    """)

    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        response, stylesheets=[css]
    )
    return response

@login_required(login_url='connexion')
def liste_niveau_etudes_option_adresse_par_option_pdf(request):
    """
    PDF : Niveau d'études, option et adresses des cadres et agents de la CNSS,
    filtré par option (toutes entités).

    Champs affichés :
      N°, Nom, Matricule, Sexe, Grade actuel,
      Niveau d'études, Adresse, Entité

    ⚠ L'option N'APPARAÎT PAS en colonne : elle est déjà dans le titre.
    """
    option_choisie = (request.GET.get("option") or "").strip()

    # Base : seulement les Actifs
    qs = Employe.objects.filter(statut__iexact="Actif")
    if option_choisie:
        qs = qs.filter(option__icontains=option_choisie)

    agents = list(qs)

    # Tri : ordre de grade + nom + prénom
    def sort_key(emp):
        grade_label = _normalize_grade(emp.grade_actuel)
        rang = grade_priority(grade_label)
        nom = (emp.nom or "").upper()
        prenom = (emp.prenom or "").upper()
        return (rang, nom, prenom)

    agents_sorted = sorted(agents, key=sort_key)

    # Titre spécifique CNSS + Option
    titre_base = "Niveau d'études, option et adresses des cadres et agents de la CNSS"
    if option_choisie:
        titre = f"{titre_base} – Option : {option_choisie}"
    else:
        titre = f"{titre_base} – Toutes options"

    # Colonnes du tableau (sans Option)
    colonnes = [
        "N°",
        "Nom",
        "Matricule",
        "Sexe",
        "Grade actuel",
        "Niveau d'études",
        "Adresse",
        "Entité",
    ]

    # donnees = [idx, nom, matricule, sexe, grade, niveau, adresse, entite]
    donnees = []
    for idx, emp in enumerate(agents_sorted, start=1):
        donnees.append([
            idx,                                         # N°
            (emp.nom or "-"),                            # Nom
            emp.matricule or "-",                        # Matricule
            emp.sexe or "-",                             # Sexe
            _normalize_grade(emp.grade_actuel) or "-",   # Grade actuel
            getattr(emp, "niveau_etudes", None) or "-",  # Niveau d'études
            getattr(emp, "adresse", None) or "-",        # Adresse
            getattr(emp, "entite", None) or "-",         # Entité
        ])

    try:
        html_string = render_to_string(
            "personnel/liste_niveau_etudes_option_adresse_par_option_pdf.html",
            {
                "titre": titre,
                "colonnes": colonnes,
                "donnees": donnees,
                "today": now(),
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            },
        )
    except TemplateDoesNotExist:
        return _pdf_fallback(titre, donnees, colonnes)

    response = HttpResponse(content_type="application/pdf")
    safe_option = (option_choisie or "toutes_options").replace(" ", "_")
    response["Content-Disposition"] = (
        f'inline; filename="niveau_etudes_option_adresse_CNSS_{safe_option}.pdf"'
    )

    css = CSS(string="""
        @page {
            size: A4 landscape;
            margin: 1cm;
        }

        h2 {
            text-align: center;
            font-weight: bold;
            text-decoration: underline;
            margin-bottom: 10px;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            font-size: 11px;
            margin-top: 10px;
        }

        th, td {
            border: 0.5pt solid #555;
            padding: 3px 4px;
        }

        th {
            background-color: #f2f2f2;
            text-align: center;
        }
    """)
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(
        response, stylesheets=[css]
    )
    return response

@login_required(login_url='connexion')
def liste_cadres_direction_pdf(request):
    entite = request.GET.get('entite')
    cadres = Employe.objects.filter(
        statut='Actif',
        entite=entite,
        fonction__in=ORDRE_FONCTIONS_DG
    )
    cadres = sorted(cadres, key=lambda x: (_fonction_priority(ORDRE_FONCTIONS_DG, x.fonction), x.nom or ""))

    lignes = []
    for i, agent in enumerate(cadres, start=1):
        age = calcul_age(agent.date_naissance)
        duree_affectation = "-"
        if agent.date_affectation:
            duree_affectation = format_duree(calcul_duree_detaillee(agent.date_affectation))
        lignes.append((
            i,
            agent.nom or "-",
            agent.matricule or "-",
            agent.grade_actuel or "-",
            agent.sexe or "-",
            agent.fonction or "-",
            agent.date_affectation.strftime('%d/%m/%Y') if agent.date_affectation else '-',
            duree_affectation,
            f"{age} an" if age == 1 else f"{age} ans" if age is not None else "-",
        ))

    try:
        html_string = render_to_string("personnel/liste_cadres_direction_pdf.html", {
            'entite': entite,
            'lignes': lignes,
            'logo_b64': _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        return _pdf_fallback("Cadres de direction", lignes)

    css = CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[css])
    return HttpResponse(pdf, content_type='application/pdf')


def grade_priority(grade):
    return _fonction_priority(ORDRE_GRADES, grade)


# ---------- ✅ PAGE HTML INTERACTIVE (bouton Filtrer + Export PDF) ----------
@login_required(login_url='connexion')
def liste_retraitables_page(request):
    """
    Page HTML interactive (JS) pour filtrer les retraitables par catégories.
    - Élagage : exclut toute personne dont l'année des 66 ans <= année courante.
    - Catégories calculées à partir de l'année des 65 ans.
    - Ajout de la date de départ en retraite (65 ans).
    """
    today = timezone.localdate()
    current_year = today.year

    qs = Employe.objects.exclude(date_naissance__isnull=True).only(
        "nom", "matricule", "grade_actuel", "sexe", "date_naissance", "entite"
    )

    retraitables = []
    for agent in qs:
        dnaiss = agent.date_naissance
        if not dnaiss:
            continue

        # Élagage 66+
        if (dnaiss.year + EXCLUSION_AGE) <= current_year:
            continue

        cat = _categorie_retraite(dnaiss, current_year)
        if not cat:
            continue

        age = _age_aujourdhui(dnaiss, today)
        age_str = "-" if age is None else (f"{age} an" if age == 1 else f"{age} ans")
        ddr = _date_depart_retraite(dnaiss)  # ✅ +65 ans

        retraitables.append({
            "nom": agent.nom or "",
            "matricule": agent.matricule or "",
            "grade": agent.grade_actuel or "",
            "sexe": agent.sexe or "",
            "date_naissance": dnaiss,
            "age_str": age_str,
            "date_depart_retraite": ddr,  # ✅
            "entite": agent.entite or "",
            "categorie": cat,
        })

    # Tri identique à la vue PDF
    ordre_cat = {
        "annee_en_cours": 0,
        "dans_1_an": 1,
        "dans_2_ans": 2,   # ✅ nouvelle catégorie
        "dans_3_ans": 3,
        "dans_4_ans": 4,
        "dans_5_ans": 5
    }
    retraitables.sort(
        key=lambda x: (
            ordre_cat.get(x['categorie'], 99),
            grade_priority(x['grade']),
            (x['nom'] or "").lower()
        )
    )

    try:
        return render(request, "personnel/liste_retraitables_page.html", {
            "retraitables": retraitables,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        # Si le template HTML interactif manque, fallback PDF minimal avec la nouvelle colonne
        rows = [[
            r['nom'], r['matricule'], r['grade'], r['sexe'],
            r['date_naissance'].strftime("%d/%m/%Y") if r['date_naissance'] else "-",
            r['age_str'],
            r['date_depart_retraite'].strftime("%d/%m/%Y") if r['date_depart_retraite'] else "-",
            r['entite'], r['categorie']
        ] for r in retraitables]
        return _pdf_fallback(
            "Cadres & agents retraitables (page manquante)",
            rows,
            ["Nom","Matricule","Grade","Sexe","Date de naissance","Âge","Date départ retraite","Entité","Catégorie"]
        )


# ---------- ✅ RETRAITABLES PDF (élagage 66+, catégories + filtre ?categorie=) ----------
@login_required(login_url='connexion')
def liste_retraitables_pdf(request):
    """
    Produit le PDF des retraitables.
    Paramètre optionnel:
      - ?categorie in {'annee_en_cours','dans_1_an','dans_2_ans','dans_3_ans','dans_4_ans','dans_5_ans'}
    Règles:
      - Élagage 66+ (année des 66 ans <= année courante -> exclu)
      - Catégorie basée sur l'année des 65 ans.
      - Ajout de la date de départ en retraite (65 ans).
    """
    today = timezone.localdate()
    current_year = today.year
    filtre = (request.GET.get("categorie") or "").strip()
    allowed = {"annee_en_cours", "dans_1_an", "dans_2_ans", "dans_3_ans", "dans_4_ans", "dans_5_ans"}

    # ✅ Libellés officiels pour le titre
    libelles = {
        "toutes": "Liste des Cadres et Agents retraitables",
        "dans_5_ans": "Liste des Cadres et Agents retraitables dans cinq ans",
        "dans_4_ans": "Liste des Cadres et Agents retraitables dans quatre ans",
        "dans_3_ans": "Liste des Cadres et Agents retraitables dans trois ans",
        "dans_2_ans": "Liste des Cadres et Agents retraitables dans deux ans",
        "dans_1_an": "Liste des Cadres et Agents retraitables dans une année",
        "annee_en_cours": "Liste des Cadres et Agents retraitables pour l’année en cours",
    }
    titre_courant = libelles.get(filtre if filtre in allowed else "toutes")

    qs = Employe.objects.exclude(date_naissance__isnull=True).only(
        "nom", "matricule", "grade_actuel", "sexe", "date_naissance", "entite"
    )

    retraitables = []
    for agent in qs:
        dnaiss = agent.date_naissance
        if not dnaiss:
            continue

        # ✅ Élagage 66+
        if (dnaiss.year + EXCLUSION_AGE) <= current_year:
            continue

        # ✅ Catégorie
        categorie = _categorie_retraite(dnaiss, current_year)
        if not categorie:
            continue

        # ✅ Filtre éventuel depuis la page interactive
        if filtre and filtre in allowed and categorie != filtre:
            continue

        age = _age_aujourdhui(dnaiss, today)
        age_str = "-" if age is None else (f"{age} an" if age == 1 else f"{age} ans")
        ddr = _date_depart_retraite(dnaiss)  # ✅ +65 ans

        retraitables.append({
            'nom': agent.nom,
            'matricule': agent.matricule,
            'grade': agent.grade_actuel,
            'sexe': agent.sexe,
            'date_naissance': dnaiss,
            'age': age,
            'age_str': age_str,
            'date_depart_retraite': ddr,  # ✅
            'entite': agent.entite,
            'categorie': categorie,
        })

    # Tri
    ordre_cat = {
        "annee_en_cours": 0,
        "dans_1_an": 1,
        "dans_2_ans": 2,   # ✅ nouvelle catégorie
        "dans_3_ans": 3,
        "dans_4_ans": 4,
        "dans_5_ans": 5
    }
    retraitables.sort(
        key=lambda x: (
            ordre_cat.get(x['categorie'], 99),
            grade_priority(x['grade']),
            (x['nom'] or "").lower()
        )
    )

    try:
        html_string = render_to_string("personnel/liste_retraitables_pdf.html", {
            'retraitables': retraitables,
            'date': today,
            'logo_b64': _logo_b64("images/logo_cnss.png"),
            # on envoie aussi 'titre' si jamais le template le supporte
            'titre': titre_courant,
            'categorie': filtre if filtre in allowed else '',
        })
    except TemplateDoesNotExist:
        rows = [[
            r['nom'], r['matricule'], r['grade'], r['sexe'],
            r['date_naissance'].strftime("%d/%m/%Y") if r['date_naissance'] else "-",
            r['age_str'],
            r['date_depart_retraite'].strftime("%d/%m/%Y") if r['date_depart_retraite'] else "-",
            r['entite'], r['categorie']
        ] for r in retraitables]
        return _pdf_fallback(
            titre_courant,
            rows,
            ["Nom","Matricule","Grade","Sexe","Date de naissance","Âge","Date départ retraite","Entité","Catégorie"]
        )

    # ✅ Sécurisation du titre même si le template a un H2 en dur :
    # 1) Tentative de remplacement ciblé si l'id "page-title" est présent
    replaced = False
    html_new = html_string.replace(
        'id="page-title">Liste des Cadres et Agents retraitables',
        f'id="page-title">{titre_courant}'
    )
    if html_new != html_string:
        replaced = True
        html_string = html_new

    # 2) Si l’ID n’existe pas, on remplace le premier <h2>...</h2> (proprement)
    if not replaced:
        html_new = re.sub(
            r"(<h2[^>]*>)(.*?)(</h2>)",
            lambda m: f"{m.group(1)}{titre_courant}{m.group(3)}",
            html_string,
            count=1,
            flags=re.DOTALL | re.IGNORECASE
        )
        html_string = html_new

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    css = CSS(string="@page { size: A4 landscape; }")

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="cadres_agents_retraitables.pdf"'
    html.write_pdf(response, stylesheets=[css])
    return response


@login_required(login_url='connexion')
def liste_detachement_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut='En détachement').order_by('nom')
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = []
    for idx, emp in enumerate(qs, 1):
        date_debut = emp.date_statut
        date_fin = getattr(emp, 'date_fin_detachement', None)
        duree = "-" # De 2023 à ce jour
        if date_debut and date_fin:
            duree = format_duree(calcul_duree_detaillee(date_debut, date_fin))
        donnees.append([
            idx,
            emp.nom or '-',
            emp.matricule or '-',
            emp.grade_actuel or '-',
            emp.sexe or '-',
            date_debut.strftime('%d/%m/%Y') if date_debut else '-',
            date_fin.strftime('%d/%m/%Y') if date_fin else '-',
            duree,
            emp.entite or '-',
        ])

    titre = "Liste des Agents en détachement" + (f" pour l'année {year}" if year else "")

    try:
        html_string = render_to_string("personnel/liste_detachement_pdf.html", {
            "titre": titre,
            "colonnes": [
                "N°", "Nom", "Matricule", "Grade actuel", "Sexe",
                "Date détachement", "Date fin détachement", "Durée", "Entité",
            ],
            "donnees": donnees,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        return _pdf_fallback(titre, donnees)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_detachement.pdf"
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
        response,
        stylesheets=[CSS(string="@page { size: landscape; }")]
    )
    return response


@login_required(login_url='connexion')
def liste_licencies_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut="Licencié").order_by("nom")
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = []
    for i, agent in enumerate(qs, start=1):
        carriere = format_duree(calcul_duree_detaillee(agent.date_engagement, agent.date_statut))
        carriere = nettoyer_unite_ans(carriere)
        donnees.append([
            i,
            agent.nom or "-",
            agent.matricule or "-",
            agent.grade_actuel or "-",
            agent.sexe or "-",
            agent.date_engagement.strftime("%d/%m/%Y") if agent.date_engagement else "-",
            agent.date_statut.strftime("%d/%m/%Y") if agent.date_statut else "-",
            carriere,
            agent.entite or "-",
        ])

    titre = "Liste des Agents licenciés" + (f" en {year}" if year else "")

    try:
        html_string = render_to_string("personnel/liste_licencies_pdf.html", {
            "titre": titre,
            "colonnes": ["N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Date engagement", "Date licenciement", "Carrière", "Entité"],
            "donnees": donnees,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        return _pdf_fallback(titre, donnees)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    css = CSS(string='@page { size: landscape; }')
    pdf = html.write_pdf(stylesheets=[css])
    return HttpResponse(pdf, content_type='application/pdf')


@login_required(login_url='connexion')
def liste_disponibilite_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut="Mise en disponibilité").order_by('nom')
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = {}
    for i, agent in enumerate(qs, start=1):
        duree = "-"
        if agent.date_statut:
            duree = format_duree(calcul_duree_detaillee(agent.date_statut))
            duree = nettoyer_unite_ans(duree)

        donnees[i] = {
            'nom': agent.nom or "-",
            'matricule': agent.matricule or "-",
            'grade': agent.grade_actuel or "-",
            'sexe': agent.sexe or "-",
            'date_dispo': agent.date_statut.strftime('%d/%m/%Y') if agent.date_statut else "-",
            'duree': duree,
            'entite': agent.entite or "-",
        }

    titre = "Liste des Agents mis en disponibilité" + (f" en {year}" if year else "")

    try:
        html_string = render_to_string("personnel/liste_disponibilite_pdf.html", {
            'titre': titre,
            'donnees': donnees,
            'logo_b64': _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        # transformer dict -> rows
        rows = [[k] + list(v.values()) for k, v in donnees.items()]
        return _pdf_fallback(titre, rows)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf_file = html.write_pdf()
    return HttpResponse(pdf_file, content_type='application/pdf')


@login_required(login_url='connexion')
def liste_retraites_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut='Mise à la retraite').order_by('nom')
    if year:
        qs = qs.filter(date_statut__year=year)

    agents = list(qs)
    for emp in agents:
        emp.age_depart = "-"
        emp.carriere = "-"
        if emp.date_naissance and emp.date_statut:
            age = date.today().year - emp.date_naissance.year - (
                (date.today().month, date.today().day) < (emp.date_naissance.month, emp.date_naissance.day)
            )
            emp.age_depart = f"{age} an" if age == 1 else f"{age} ans"
        # ✅ Carrière détaillée en années, mois, jours
        if emp.date_engagement and emp.date_statut:
            emp.carriere = format_duree(calcul_duree_detaillee(emp.date_engagement, emp.date_statut))

    agents = list(enumerate(agents, start=1))

    # --- Titre : ajoute "(Situation à date)" uniquement si year == année courante ---
    current_year = timezone.localdate().year
    titre_base = "Liste des Agents retraités" + (f" en {year}" if year else "")
    titre = titre_base + " (Situation à date)" if (year and year == current_year) else titre_base

    try:
        html_string = render_to_string("personnel/liste_retraites_pdf.html", {
            "titre": titre,
            "agents": agents,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        rows = [[i, a.nom or "-", a.matricule or "-", a.grade_actuel or "-", a.sexe or "-"] for i, a in agents]
        return _pdf_fallback(titre, rows)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_retraites.pdf"
    css = CSS(string='''
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; font-weight: bold; text-decoration: underline; margin-bottom: 10px; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }
        th { background-color: #f2f2f2; text-align: center; padding: 6px; border: 1px solid #000; }
        td { text-align: center; padding: 6px; border: 1px solid #000; }
        td.left { text-align: left; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


def calcul_age_deces(date_naissance, date_deces=None):
    if not date_naissance:
        return "-"

    date_fin = date_deces if date_deces else date.today()
    jours_total = (date_fin - date_naissance).days
    if jours_total < 30:
        return f"{jours_total} jours"
    elif jours_total < 365:
        mois = jours_total // 30
        return f"{mois} mois"
    else:
        ans = jours_total // 365
        return f"{ans} an{'s' if ans > 1 else ''}"


@login_required(login_url='connexion')
def liste_decedes_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut="Décédé").order_by("nom")
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = []
    for i, emp in enumerate(qs, start=1):
        age_deces = "-"
        if emp.date_naissance:
            age_deces = calcul_age_deces(emp.date_naissance, emp.date_statut)
        donnees.append([
            i,
            emp.nom or "-",
            emp.matricule or "-",
            emp.sexe or "-",
            emp.date_naissance.strftime("%d/%m/%Y") if emp.date_naissance else "-",
            emp.date_statut.strftime("%d/%m/%Y") if emp.date_statut else "-",
            age_deces,
            emp.entite or "-",
        ])

    # Suffixe "(De 2023 à ce jour)" UNIQUEMENT si l'année demandée == année en cours
    current_year = timezone.localdate().year
    suffix = " (De 2023 à ce jour)" if (year == current_year) else ""

    titre = "Liste des Agents décédés" + (f" en {year}" if year else "") + suffix

    try:
        html_string = render_to_string("personnel/liste_decedes_pdf.html", {
            "titre": titre,
            "colonnes": ["N°", "Nom", "Matricule", "Sexe", "Date de naissance", "Date décès", "Âge décédé", "Entité"],
            "donnees": donnees,
            "today": now(),
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        return _pdf_fallback(titre, donnees)

    css = CSS(string="""
        @page { size: A4 landscape; margin: 1cm; }
        h2 { text-align: center; font-weight: bold; text-decoration: underline; }
        table { width: 100%; border-collapse: collapse; font-size: 12px; margin-top: 10px; }
        th { background-color: #f2f2f2; text-align: center; }
        td { text-align: center; }
        th, td { border: 1px solid #000; padding: 5px; }
        td.left { text-align: left; }
        td.age { text-align: center; }
        td.entite { text-align: left; }
    """)
    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_decedes.pdf"
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


@login_required(login_url='connexion')
def liste_demissionnaires_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut='Démission').order_by('nom')
    if year:
        qs = qs.filter(date_statut__year=year)

    agents = list(qs)
    for emp in agents:
        emp.carriere = "-" # De 2023 à ce jour
        if emp.date_engagement and emp.date_statut:
            emp.carriere = format_duree(calcul_duree_detaillee(emp.date_engagement, emp.date_statut))
    agents = list(enumerate(agents, start=1))

    titre = "Liste des Agents ayant démissionné" + (f" en {year}" if year else "")

    try:
        html_string = render_to_string("personnel/liste_demissionnaires_pdf.html", {
            "titre": titre,
            "agents": agents,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        rows = [[i, a.nom or "-", a.matricule or "-", a.grade_actuel or "-", a.sexe or "-"] for i, a in agents]
        return _pdf_fallback(titre, rows)

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=liste_demissionnaires.pdf"
    css = CSS(string='@page { size: A4 landscape; margin: 1cm; }')
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(response, stylesheets=[css])
    return response


@login_required(login_url='connexion')
def liste_effectif_par_entite_pdf(request):
    """
    Effectif (nombre) d'agents par entité, **uniquement** pour les agents au statut 'Actif'.
    """
    effectifs = (
        Employe.objects
        .filter(statut__iexact="Actif")
        .values('entite')
        .annotate(total=Count('id'))
        .order_by('total')
    )
    total_general = sum(item['total'] for item in effectifs)

    donnees = []
    for i, item in enumerate(effectifs, start=1):
        donnees.append({
            'numero': i,
            'entite': item['entite'] or "-",
            'effectif': item['total'],
        })

    try:
        html_string = render_to_string(
            "personnel/liste_effectif_par_entite_pdf.html",
            {
                "donnees": donnees,
                "total_general": total_general,
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            }
        )
    except TemplateDoesNotExist:
        rows = [[d['numero'], d['entite'], d['effectif']] for d in donnees]
        return _pdf_fallback("Effectif par entité (Actifs)", rows, ["N°","Entité","Effectif"])

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    result = html.write_pdf(stylesheets=[CSS(string='@page { size: A4 portrait; margin: 1cm }')])

    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'inline; filename="effectif_par_entite.pdf"'
    response.write(result)
    return response


@login_required(login_url='connexion')
def liste_effectif_par_grade_pdf(request):
    """
    PDF détaillé par grade pour une entité donnée **en ne comptant que les agents Actifs**.
    Attend ?entite=... dans la query string.
    """
    GRADES_ORDONNES = ORDRE_GRADES[:]
    entite_choisie = (request.GET.get("entite") or "").strip()
    if not entite_choisie:
        return redirect("personnel:effectif_detaille_par_grade")

    data = []
    total_general = 0
    for idx, grade in enumerate(GRADES_ORDONNES, start=1):
        count = Employe.objects.filter(
            entite=entite_choisie,
            grade_actuel=grade,
            statut__iexact="Actif"
        ).count()
        data.append({"numero": idx, "grade": grade, "effectif": count})
        total_general += count

    try:
        html_string = render_to_string(
            "personnel/effectif_par_grade_pdf.html",
            {
                "titre": f"Effectif des Agents par Grade : {entite_choisie}",
                "data": data,
                "donnees": data,          # alias pour éviter VariableDoesNotExist
                "total_general": total_general,
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            }
        )
    except TemplateDoesNotExist:
        rows = [[d["numero"], d["grade"], d["effectif"]] for d in data]
        return _pdf_fallback(f"Effectif par grade : {entite_choisie}", rows, ["N°","Grade","Effectif"])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = "inline; filename=effectif_par_grade.pdf"
    HTML(string=html_string, base_url=request.build_absolute_uri('/')).write_pdf(
        response,
        stylesheets=[CSS(string="@page { size: portrait; margin: 1cm; }")]
    )
    return response


# ---------- ✅ Effectif ACTIFS par grade (toutes entités) ----------
@login_required(login_url='connexion')
def effectif_actifs_par_grade_pdf(request):
    data_qs = (
        Employe.objects.filter(statut__iexact="Actif")
        .values("grade_actuel")
        .annotate(total=Count("id"))
    )
    counts = {row["grade_actuel"]: row["total"] for row in data_qs}

    donnees = []
    total_general = 0
    for i, grade in enumerate(ORDRE_GRADES, start=1):
        n = counts.get(grade, 0)
        donnees.append([i, grade, n])
        total_general += n

    try:
        html_string = render_to_string(
            "personnel/effectif_actifs_par_grade_pdf.html",
            {
                "titre": "Effectif des agents actifs par grade",
                "colonnes": ["N°", "Grade", "Effectif (Actifs)"],
                "donnees": donnees,
                "total_general": total_general,
                "today": now(),
                "logo_b64": _logo_b64("images/logo_cnss.png"),
            }
        )
    except TemplateDoesNotExist:
        return _pdf_fallback("Effectif des agents actifs par grade", donnees,
                             ["N°","Grade","Effectif (Actifs)"])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="effectif_actifs_par_grade.pdf"'
    css = CSS(string='''
        @page { size: A4 landscape; margin: 14mm; }
        h1, h2 { text-align: center; text-decoration: underline; margin: 0 0 8px 0; }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; margin-top: 8px; font-size: 12px; }
        th, td { border: 1px solid #000; padding: 6px; }
        th { background: #eee; text-align: center; }
        td:nth-child(1), td:nth-child(3) { text-align: center; width: 80px; }
        td:nth-child(2) { text-align: left; }
        tfoot td { font-weight: bold; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[css])
    return response


# ---------- ✅ Liste détaillée des Actifs par grade (ENTITÉ CHOISIE) ----------
_NORMALIZE_GRADE = {
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
    k = label.strip().lower().replace("é", "e").replace("œ", "oe")
    k = k.replace("1ère", "1ere").replace("1ere", "1ere")
    k = k.replace("2ème", "2eme").replace("2eme", "2eme")
    return _NORMALIZE_GRADE.get(k, label.strip())


@login_required(login_url='connexion')
def liste_agents_ayant_ete_licencies_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut="Licencié").order_by("nom")
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = {}
    for i, agent in enumerate(qs, start=1):
        carriere = "-"
        if agent.date_engagement and agent.date_statut:
            carriere = format_duree(calcul_duree_detaillee(agent.date_engagement, agent.date_statut))
        donnees[i] = {
            "nom": agent.nom or "-",
            "matricule": agent.matricule or "-",
            "grade": agent.grade_actuel or "-",
            "sexe": agent.sexe or "-",
            "date_engagement": agent.date_engagement.strftime("%d/%m/%Y") if agent.date_engagement else "-",
            "date_statut": agent.date_statut.strftime("%d/%m/%Y") if agent.date_statut else "-",
            "carriere": carriere,
            "entite": agent.entite or "-",
        }

    titre = "Liste des Agents licenciés" + (f" en {year}" if year else "")
    try:
        html_string = render_to_string("personnel/liste_agents_ayant_ete_licencies_pdf.html", {
            "titre": titre,
            "donnees": donnees,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        rows = [[k] + list(v.values()) for k, v in donnees.items()]
        return _pdf_fallback(titre, rows)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[CSS(string='@page { size: A4 landscape; margin: 1cm; }')])
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="agents_ayant_ete_licencies.pdf"'
    return response


@login_required(login_url='connexion')
def liste_agents_mis_en_disponibilite_pdf(request):
    year = _get_year(request)
    qs = Employe.objects.filter(statut="Mise en disponibilité").order_by("nom")
    if year:
        qs = qs.filter(date_statut__year=year)

    donnees = {}
    for i, agent in enumerate(qs, start=1):
        date_dispo = agent.date_statut
        date_fin_dispo = getattr(agent, 'date_fin_disponibilite', None)
        if date_dispo and date_fin_dispo:
            duree = format_duree(calcul_duree_detaillee(date_dispo, date_fin_dispo))
        else:
            duree = "-"
            date_fin_dispo = None

        donnees[i] = {
            "nom": agent.nom or "-",
            "matricule": agent.matricule or "-",
            "grade": agent.grade_actuel or "-",
            "sexe": agent.sexe or "-",
            "date_dispo": date_dispo.strftime("%d/%m/%Y") if date_dispo else "-",
            "date_fin_dispo": date_fin_dispo.strftime("%d/%m/%Y") if date_fin_dispo else "-",
            "duree": duree,
            "entite": agent.entite or "-",
        }

    titre = "Liste des Agents mis en disponibilité" + (f" en {year}" if year else "")

    try:
        html_string = render_to_string("personnel/liste_agents_mis_en_disponibilite_pdf.html", {
            "titre": titre,
            "donnees": donnees,
            "logo_b64": _logo_b64("images/logo_cnss.png"),
        })
    except TemplateDoesNotExist:
        rows = [[k] + list(v.values()) for k, v in donnees.items()]
        return _pdf_fallback(titre, rows)

    html = HTML(string=html_string, base_url=request.build_absolute_uri('/'))
    pdf = html.write_pdf(stylesheets=[CSS(string='@page { size: A4 landscape; margin: 1cm; }')])
    response = HttpResponse(pdf, content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="agents_mis_en_disponibilite.pdf"'
    return response


# ---------- ✅ Liste Actifs filtrée (PDF) ----------
@login_required(login_url='connexion')
def liste_actifs_filtre_pdf(request):
    """
    PDF des agents Actifs avec filtres ?entite=... & ?grade=...
    """
    entite = (request.GET.get("entite") or "").strip()
    grade = (request.GET.get("grade") or "").strip()

    qs = Employe.objects.filter(statut__iexact="Actif")
    if entite:
        qs = qs.filter(entite=entite)
    if grade:
        qs = qs.filter(grade_actuel=grade)
    qs = qs.order_by("matricule")

    try:
        from .models import ENTITE_CHOICES, GRADE_ACTUEL_CHOICES  # type: ignore
    except Exception:
        ENTITE_CHOICES, GRADE_ACTUEL_CHOICES = None, None

    entite_label = _label_from_choices(entite, ENTITE_CHOICES) if ENTITE_CHOICES else (entite or None)
    grade_label  = _label_from_choices(grade,  GRADE_ACTUEL_CHOICES) if GRADE_ACTUEL_CHOICES else (grade or None)
    titre = f"Tableau des agents actifs : {entite_label or 'Toutes entités'} – {grade_label or 'Tous grades'}"

    try:
        html_string = render_to_string(
            "personnel/liste_actifs_filtre_pdf.html",
            {"titre": titre, "agents": qs, "logo_b64": _logo_b64("images/logo_cnss.png")}
        )
    except TemplateDoesNotExist:
        rows = [[a.nom or "-", a.matricule or "-", a.fonction or "-"] for a in qs]
        return _pdf_fallback(titre, rows, ["Nom","Matricule","Fonction"])

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = 'inline; filename="actifs_filtre.pdf"'
    css = CSS(string='''
        @page { size: A4 portrait; margin: 14mm; }
        h2 { text-align: center; text-decoration: underline; margin: 0 0 12px 0; }
        table { width: 100%; border-collapse: collapse; table-layout: fixed; }
        th, td { border: 1px solid #aaa; padding: 6px; font-size: 12px; }
        th { background: #f0f0f0; text-align: center; }
    ''')
    HTML(string=html_string, base_url=request.build_absolute_uri("/")).write_pdf(response, stylesheets=[css])
    return response


# ---------- ✅ Alias pour compatibilité ----------
effectif_detaille_par_grade_pdf = liste_effectif_par_grade_pdf
