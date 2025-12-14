# personnel/vue_liste_reponsables_coordonnateurs.py
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Employe


# Fonctions ciblées (exactes)
FONCTIONS_CIBLES = [
    "Responsable",
    "Responsable a.i",
    "Coordonnateur",
    "Coordonnateur a.i",
]

# Listes utilisées pour une éventuelle surbrillance côté template
FONCTIONS_SURBRILLANCE_BLEUE = ["Responsable a.i", "Coordonnateur a.i"]
GRADES_SURBRILLANCE_VERTE = ["Chef de Sce Adjt", "Chef de Section", "Rédacteur Ppal", "Rédacteur"]


def _years_since(d):
    """Durée en années révolues depuis la date `d` (ou '-')."""
    if not d:
        return "-"
    t = date.today()
    years = t.year - d.year - ((t.month, t.day) < (d.month, d.day))
    return f"{years} an" if years == 1 else f"{years} ans"


@login_required
def liste_responsables_coordonnateurs(request):
    # Entité choisie (optionnelle)
    entite_choisie = (request.GET.get("entite") or "").strip()

    # Filtre robuste : correspondances exactes + variantes tolérantes
    filtre_fonction = (
        Q(fonction__in=FONCTIONS_CIBLES)
        | Q(fonction__icontains="responsable")
        | Q(fonction__icontains="coordonnateur")
    )

    base_qs = Employe.objects.filter(filtre_fonction)

    # Entités disponibles (nettoyées, uniques, triées)
    entites_nettoyees = (
        base_qs.exclude(entite__isnull=True)
        .exclude(entite__exact="")
        .values_list("entite", flat=True)
        .distinct()
        .order_by("entite")
    )

    # Filtrage par entité (si fourni)
    if entite_choisie:
        qs = base_qs.filter(entite__iexact=entite_choisie)
        titre = f"Liste des Responsables et Coordonnateurs du Service - {entite_choisie}"
    else:
        qs = base_qs
        titre = "Liste des Responsables et Coordonnateurs du Service"

    # Tri lisible
    qs = qs.order_by("entite", "nom", "prenom")

    # Construction des lignes pour le template
    donnees = []
    for idx, emp in enumerate(qs, start=1):
        donnees.append([
            idx,
            emp.nom or "-",
            emp.matricule or "-",
            emp.grade_actuel or "-",
            emp.sexe or "-",
            emp.service or "-",
            emp.fonction or "-",
            emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
            _years_since(emp.date_affectation),
            emp.entite or "-",
        ])

    colonnes = [
        "N°", "Nom", "Matricule", "Grade actuel", "Sexe", "Service",
        "Fonction", "Date affectation", "Durée affectation", "Entité",
    ]

    return render(
        request,
        "personnel/liste_responsables_coordonnateurs.html",
        {
            "donnees": donnees,
            "colonnes": colonnes,
            "titre": titre,
            "entites": list(entites_nettoyees),
            "selected_entite": entite_choisie,   # compatibilité avec templates existants
            "entite_choisie": entite_choisie,    # (si utilisé ailleurs)
            # Optionnel : listes pour surbrillance dans le template
            "fonctions_surbrillance_bleue": FONCTIONS_SURBRILLANCE_BLEUE,
            "grades_surbrillance_verte": GRADES_SURBRILLANCE_VERTE,
        },
    )
