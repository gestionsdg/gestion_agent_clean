from django.urls import path, include
from django.contrib.auth import views as auth_views  # Pour la connexion
from . import views
from .views import (
    liste_employes, ajouter_employe, modifier_employe, logout_view,
    effectif_detaille_par_grade,  # ✅ Ajout ici
)
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
    liste_total_agents_pdf,
    liste_agents_ayant_ete_licencies_pdf,
    effectif_detaille_par_grade_pdf,  # ✅ Ajout ici
)
from .vue_liste_controleurs import liste_controleurs_par_entite
from .vue_liste_responsables_coordonnateurs import liste_responsables_coordonnateurs
from .vue_effectif_controleurs import tableau_controleurs_cnss

urlpatterns = [
    # --- Liste principale ---
    path('liste/', liste_employes, name='liste_employes'),

    # --- Ajout / Modification / Fiche ---
    path('employes/ajouter/', ajouter_employe, name='ajouter_employe'),
    path('employes/modifier/<int:pk>/', modifier_employe, name='modifier_employe'),
    path('employes/fiche/<int:pk>/', fiche_employe_pdf, name='fiche_employe_pdf'),

    # --- Listes web ---
    path('employes/actifs-entite/', include('personnel.urls_export')),  # Routes export
    path('filtrage/', include('personnel.urls_filtrage')),  # ✅ Ajout pour les routes filtrage

    # --- PDF ---
    path('employes/actifs-entite/pdf/', liste_actifs_par_entite_pdf, name='liste_actifs_par_entite_pdf'),
    path('employes/cadres-direction/pdf/', liste_cadres_direction_pdf, name='liste_cadres_direction_pdf'),
    path('employes/retraitables/pdf/', liste_retraitables_pdf, name='liste_retraitables_pdf'),
    path('employes/retraites/pdf/', liste_retraites_pdf, name='liste_retraites_pdf'),
    path('employes/decedes/pdf/', liste_decedes_pdf, name='liste_decedes_pdf'),
    path('employes/detachement/pdf/', liste_detachement_pdf, name='liste_detachement_pdf'),
    path('employes/demissionnaires/pdf/', liste_demissionnaires_pdf, name='liste_demissionnaires_pdf'),
    path('employes/licencies/pdf/', liste_licencies_pdf, name='liste_licencies_pdf'),
    path('employes/disponibilites/pdf/', liste_disponibilite_pdf, name='liste_disponibilite_pdf'),
    path('employes/responsables-pdf/', liste_responsables_par_entite_pdf, name='liste_responsables_pdf'),
    path('employes/total/pdf/', liste_total_agents_pdf, name='liste_total_agents_pdf'),
    path('pdf/agents_ayant_ete_licencies/', liste_agents_ayant_ete_licencies_pdf, name='liste_agents_ayant_ete_licencies_pdf'),

    # --- Contrôleurs et coordonnateurs ---
    path('controleurs/', liste_controleurs_par_entite, name='liste_controleurs'),
    path('controleurs/pdf/', liste_controleurs_pdf, name='liste_controleurs_pdf'),
    path('controleurs-cnss/', tableau_controleurs_cnss, name='tableau_controleurs_cnss'),

    path('responsables-coordonnateurs/', liste_responsables_coordonnateurs, name='liste_responsables_coordonnateurs'),
    path('responsables-coordonnateurs/pdf/', liste_responsables_coordonnateurs_pdf, name='liste_responsables_coordonnateurs_pdf'),

    # --- Nouvelles routes : Effectif par grade ---
    path('effectif-par-grade/', effectif_detaille_par_grade, name='effectif_detaille_par_grade'),
    path('pdf/effectif-par-grade/', effectif_detaille_par_grade_pdf, name='effectif_detaille_par_grade_pdf'),

    # --- Déconnexion ---
    path('logout/', logout_view, name='logout'),

    # --- Connexion ---
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
]
