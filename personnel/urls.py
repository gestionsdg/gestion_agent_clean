# personnel/urls.py
from django.urls import path, include
from django.views.generic import RedirectView
from . import views_export, views_pdf_weasyprint

# Vues HTML principales
from .views import (
    liste_employes,
    ajouter_employe,
    modifier_employe,
    effectif_detaille_par_grade,  # Vue web (HTML)
)
from .views_dashboard import tableau_de_bord  # ✅ Dashboard protégé

# Vues PDF (WeasyPrint) — on N’IMPORTE PAS liste_actifs_par_grade_detaille_pdf ici
from .views_pdf_weasyprint import (
    fiche_employe_pdf,
    liste_responsables_par_entite_pdf,
    liste_controleurs_pdf,
    liste_responsables_coordonnateurs_pdf,
    liste_actifs_par_entite_pdf,
    liste_cadres_direction_pdf,
    liste_retraitables_pdf,
    liste_retraites_pdf,
    liste_decedes_pdf,
    liste_detachement_pdf,
    liste_demissionnaires_pdf,
    liste_licencies_pdf,
    liste_disponibilite_pdf,
    liste_agents_ayant_ete_licencies_pdf,
    liste_effectif_par_entite_pdf,        # PDF effectif par entité
    effectif_actifs_par_grade_pdf,        # ✅ PDF effectif ACTIFS par grade (toutes entités)
    liste_niveau_etudes_option_adresse_pdf,          # ✅ PDF niveau études / option / adresse (par entité)
    liste_niveau_etudes_option_adresse_par_option_pdf,  # ✅ PDF niveau études / adresses PAR OPTION (toute CNSS)
)

# ✅ Alias robuste : si effectif_detaille_par_grade_pdf n’existe pas,
# on utilise liste_effectif_par_grade_pdf sous le même nom.
try:
    from .views_pdf_weasyprint import effectif_detaille_par_grade_pdf  # noqa: F401
except ImportError:
    from .views_pdf_weasyprint import (
        liste_effectif_par_grade_pdf as effectif_detaille_par_grade_pdf
    )

# Autres vues web (tableaux spécifiques)
from .vue_liste_controleurs import liste_controleurs_par_entite
from .vue_liste_responsables_coordonnateurs import liste_responsables_coordonnateurs
from .vue_effectif_controleurs import tableau_controleurs_cnss

# Totaux / Exports + ✅ HTML effectif ACTIFS par grade
from .views_export import (
    total_agents,
    agents_actifs,
    export_employes_excel_complet,
    effectif_actifs_par_grade,      # ✅ HTML effectif ACTIFS par grade (toutes entités)
)

app_name = "personnel"

urlpatterns = [
    # ---------- Dashboard (protégé) ----------
    path("dashboard/", tableau_de_bord, name="dashboard"),

    # ---------- Liste principale / CRUD ----------
    path("employes/", liste_employes, name="liste_employes"),
    path("liste/", RedirectView.as_view(pattern_name="personnel:liste_employes", permanent=False)),
    path("employes/ajouter/", ajouter_employe, name="ajouter_employe"),
    path("employes/modifier/<int:pk>/", modifier_employe, name="modifier_employe"),

    # Fiche PDF individuelle
    path("employes/fiche/<int:pk>/", fiche_employe_pdf, name="fiche_employe_pdf"),

    # ---------- Groupes de routes incluses ----------
    path("employes/actifs-entite/", include("personnel.urls_filtrage")),   # (si nécessaire)
    path("filtrage/", include("personnel.urls_filtrage")),                 # (si nécessaire)

    # ---------- ✅ RETRAITABLES (HTML + PDF) ----------
    # Page HTML interactive (filtrer + bouton d'impression)
    path("employes/retraitables/", views_pdf_weasyprint.liste_retraitables_page, name="liste_retraitables_page"),
    # PDF (filtré optionnellement par ?categorie=...)
    path("employes/retraitables/pdf/", liste_retraitables_pdf, name="liste_retraitables_pdf"),

    # ---------- PDF (autres listes) ----------
    path("employes/actifs-entite/pdf/", liste_actifs_par_entite_pdf, name="liste_actifs_par_entite_pdf"),
    path("employes/cadres-direction/pdf/", liste_cadres_direction_pdf, name="liste_cadres_direction_pdf"),
    path("employes/retraites/pdf/", liste_retraites_pdf, name="liste_retraites_pdf"),
    path("employes/decedes/pdf/", liste_decedes_pdf, name="liste_decedes_pdf"),
    path("employes/detachement/pdf/", liste_detachement_pdf, name="liste_detachement_pdf"),
    path("employes/demissionnaires/pdf/", liste_demissionnaires_pdf, name="liste_demissionnaires_pdf"),
    path("employes/licencies/pdf/", liste_licencies_pdf, name="liste_licencies_pdf"),
    path("employes/disponibilites/pdf/", liste_disponibilite_pdf, name="liste_disponibilite_pdf"),
    path("employes/responsables-pdf/", liste_responsables_par_entite_pdf, name="liste_responsables_pdf"),

    # ✅ HTML : Niveau d'études, option et adresses (page)
    path(
        "employes/niveau-etudes-option-adresse/",
        views_export.liste_niveau_etudes_option_adresse,
        name="liste_niveau_etudes_option_adresse",
    ),

    # ✅ PDF : Niveau d'études / option / adresses PAR ENTITÉ
    path(
        "employes/niveau-etudes-option-adresse/pdf/",
        liste_niveau_etudes_option_adresse_pdf,
        name="liste_niveau_etudes_option_adresse_pdf",
    ),

    # ✅ NOUVEAU : PDF Niveau d'études / adresses PAR OPTION (toute la CNSS)
    path(
        "employes/niveau-etudes-option-adresse/par-option/pdf/",
        liste_niveau_etudes_option_adresse_par_option_pdf,
        name="liste_niveau_etudes_option_adresse_par_option_pdf",
    ),

    # PDF effectif par entité
    path("pdf/effectif-par-entite/", liste_effectif_par_entite_pdf, name="liste_effectif_par_entite_pdf"),

    # ---------- Listes spéciales ----------
    path(
        "pdf/agents_ayant_ete_licencies/",
        liste_agents_ayant_ete_licencies_pdf,
        name="liste_agents_ayant_ete_licencies_pdf",
    ),

    # ---------- Totaux (dashboard) ----------
    path("employes/total/", total_agents, name="total_agents"),
    path("employes/actifs/", agents_actifs, name="agents_actifs"),

    # ---------- Export Excel ----------
    path("employes/export/excel/", export_employes_excel_complet, name="export_employes_excel_complet"),

    # ---------- Contrôleurs & Coordonnateurs ----------
    path("controleurs/", liste_controleurs_par_entite, name="liste_controleurs"),
    path("controleurs/pdf/", liste_controleurs_pdf, name="liste_controleurs_pdf"),
    path("controleurs-cnss/", tableau_controleurs_cnss, name="tableau_controleurs_cnss"),

    path("responsables-coordonnateurs/", liste_responsables_coordonnateurs, name="liste_responsables_coordonnateurs"),
    path("responsables-coordonnateurs/pdf/", liste_responsables_coordonnateurs_pdf, name="liste_responsables_coordonnateurs_pdf"),

    # ---------- Effectif détaillé par grade (HTML + PDF par entité) ----------
    path("effectif-par-grade/", effectif_detaille_par_grade, name="effectif_detaille_par_grade"),
    path("pdf/effectif-par-grade/", effectif_detaille_par_grade_pdf, name="effectif_detaille_par_grade_pdf"),

    # ---------- ✅ Effectif ACTIFS par grade (toutes entités) ----------
    path("effectifs/actifs-par-grade/", effectif_actifs_par_grade, name="effectif_actifs_par_grade"),
    path("effectifs/actifs-par-grade/pdf/", effectif_actifs_par_grade_pdf, name="effectif_actifs_par_grade_pdf"),

    # ---------- Actifs filtrés (HTML + PDF) ----------
    path("actifs/filtre/", views_export.liste_actifs_filtre, name="liste_actifs_filtre"),
    path("actifs/filtre/pdf/", views_pdf_weasyprint.liste_actifs_filtre_pdf, name="liste_actifs_filtre_pdf"),
]
