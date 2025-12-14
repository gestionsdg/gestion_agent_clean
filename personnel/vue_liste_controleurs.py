# personnel/vue_liste_controleur.py
from datetime import date

from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render

from .models import Employe

# Ordre de priorité des fonctions "contrôle"
ORDRE_FONCTIONS = [
    "Coordonnateur",
    "Coordonnateur a.i",
    "Coordonnateur Adjoint",
    "Coordonnateur Adjoint Technique",
    "Coordonnateur Adjoint Administratif",
    "Contrôleur",
    "Controleur",  # variante sans accent
]


def fonction_priority(fonction: str | None) -> int:
    """Indice de priorité pour le tri des fonctions; inconnu -> fin de liste."""
    try:
        return ORDRE_FONCTIONS.index(fonction or "")
    except ValueError:
        return len(ORDRE_FONCTIONS)


def calcul_age(naissance):
    """Âge en années révolues, ou '-' si date manquante."""
    if not naissance:
        return "-"
    today = date.today()
    age = today.year - naissance.year - (
        (today.month, today.day) < (naissance.month, naissance.day)
    )
    return age


@login_required
def liste_controleurs_par_entite(request):
    # Entité choisie (optionnelle)
    entite_choisie = (request.GET.get("entite") or "").strip()

    # Filtre "contrôle" tolérant aux accents et variantes
    filtre_controle = (
        Q(service__icontains="Contrôle")
        | Q(service__icontains="Controle")
        | Q(fonction__icontains="Contrôleur")
        | Q(fonction__icontains="Controleur")
        | Q(fonction__in=ORDRE_FONCTIONS)
    )

    base_qs = Employe.objects.filter(filtre_controle)

    # Liste des entités (basée sur le même filtre, et non uniquement sur service)
    toutes_les_entites = (
        base_qs.exclude(entite__isnull=True)
        .exclude(entite__exact="")
        .values_list("entite", flat=True)
        .distinct()
        .order_by("entite")
    )

    if entite_choisie:
        qs = base_qs.filter(entite__iexact=entite_choisie)
        titre = f"Liste des Contrôleurs : {entite_choisie}"
    else:
        qs = base_qs
        titre = "Liste des Contrôleurs"

    # Tri initial basique pour la reproductibilité (avant regroupement)
    qs = qs.order_by("entite", "nom", "prenom")

    # Séparation "prioritaires" vs "autres"
    agents_prioritaires = [emp for emp in qs if emp.fonction in ORDRE_FONCTIONS]
    autres_agents = [emp for emp in qs if emp.fonction not in ORDRE_FONCTIONS]

    # Tri : priorité de fonction puis nom; puis nom pour les autres
    agents_prioritaires = sorted(
        agents_prioritaires, key=lambda emp: (fonction_priority(emp.fonction), emp.nom or "")
    )
    autres_agents = sorted(autres_agents, key=lambda emp: (emp.nom or ""))

    agents = agents_prioritaires + autres_agents

    # Construction des données pour le template
    donnees = []
    today = date.today()
    for idx, emp in enumerate(agents, 1):
        age = calcul_age(emp.date_naissance)

        # Durée d'affectation en années révolues
        duree_affectation = "-"
        if emp.date_affectation:
            delta = today.year - emp.date_affectation.year - (
                (today.month, today.day) < (emp.date_affectation.month, emp.date_affectation.day)
            )
            duree_affectation = f"{delta} an{'s' if delta != 1 else ''}"

        donnees.append(
            [
                idx,
                emp.nom or "-",
                emp.matricule or "-",
                emp.grade_actuel or "-",
                emp.sexe or "-",
                emp.fonction or "-",
                emp.date_naissance.strftime("%d/%m/%Y") if emp.date_naissance else "-",
                age,
                emp.date_affectation.strftime("%d/%m/%Y") if emp.date_affectation else "-",
                duree_affectation,
                emp.entite or "-",
            ]
        )

    colonnes = [
        "N°",
        "Nom",
        "Matricule",
        "Grade actuel",
        "Sexe",
        "Fonction",
        "Date naissance",
        "Âge",
        "Date affectation",
        "Durée affectation",
        "Entité",
    ]

    return render(
        request,
        "personnel/liste_controleurs.html",
        {
            "titre": titre,
            "colonnes": colonnes,
            "donnees": donnees,
            "entites": toutes_les_entites,
            "selected_entite": entite_choisie,
            "entite_choisie": entite_choisie,  # si un template existant l'utilise
        },
    )
