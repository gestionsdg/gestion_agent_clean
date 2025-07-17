from django.urls import path
from . import views
from .vue_liste_controleurs import liste_controleurs_par_entite
from .views_pdf_weasyprint import liste_controleurs_pdf
from .vue_liste_responsables_coordonnateurs import liste_responsables_coordonnateurs
from .views_pdf_weasyprint import liste_responsables_coordonnateurs_pdf
from .vue_effectif_controleurs import tableau_controleurs_cnss  # ✅ Ajout de la vue demandée
from personnel.views_pdf_weasyprint import liste_actifs_par_entite_pdf
from .views_pdf_weasyprint import liste_cadres_direction_pdf
from .views_pdf_weasyprint import liste_retraitables_pdf
from .views import logout_view  # adapter selon votre structure
from . import views_pdf_weasyprint
from . import views_export, views_pdf_weasyprint  # Vérifiez que les bons fichiers sont bien importés
from .views_pdf_weasyprint import (
    liste_retraites_pdf,
    liste_decedes_pdf,
    liste_detachement_pdf,
    liste_demissionnaires_pdf,
    liste_demissionnaires_pdf,
    liste_detachement_pdf,
)

from .views import (
    liste_employes,
    ajouter_employe,
    modifier_employe,
)

from .views_pdf_weasyprint import (
    fiche_employe_pdf,
    liste_responsables_par_entite_pdf,
)

from .views_export import (
    liste_actifs_par_entite,
    liste_decedes,
    liste_retraites,
    liste_demis,
    liste_detaches,
    liste_licencies,
    liste_disponibilites,
    liste_responsables_par_entite,
    export_employes_excel,
    export_employes_excel_complet,
)

urlpatterns = [
    path('employes/ajouter/', ajouter_employe, name='ajouter_employe'),
    path('employes/modifier/<int:pk>/', modifier_employe, name='modifier_employe'),
    path('employes/fiche/<int:pk>/', fiche_employe_pdf, name='fiche_employe_pdf'),

    path('employes/actifs-entite/', liste_actifs_par_entite, name='liste_actifs_entite'),
    path('employes/actifs-entite/pdf/', liste_actifs_par_entite_pdf, name='liste_actifs_par_entite_pdf'),
    path('employes/decedes/', liste_decedes, name='liste_decedes'),
    path('employes/retraites/', liste_retraites, name='liste_retraites'),
    path('employes/demissionnaires/', liste_demis, name='liste_demis'),
    path('employes/detaches/', liste_detaches, name='liste_detaches'),
    path('employes/detaches/pdf/', views_pdf_weasyprint.liste_detaches_pdf, name='liste_detaches_pdf'),
    path('employes/licencies/', liste_licencies, name='liste_licencies'),
    path('employes/disponibilites/', liste_disponibilites, name='liste_disponibilites'),

    path('employes/responsables/', liste_responsables_par_entite, name='liste_responsables'),
    path('employes/responsables-pdf/', liste_responsables_par_entite_pdf, name='liste_responsables_pdf'),

    path('employes/export-excel/', export_employes_excel, name='export_employes_excel'),
    path('employes/export-excel-complet/', export_employes_excel_complet, name='export_employes_excel_complet'),

    path('controleurs/', liste_controleurs_par_entite, name='liste_controleurs'),
    path('controleurs/pdf/', liste_controleurs_pdf, name='liste_controleurs_pdf'),

    path('responsables-coordonnateurs/', liste_responsables_coordonnateurs, name='liste_responsables_coordonnateurs'),
    path('responsables-coordonnateurs/pdf/', liste_responsables_coordonnateurs_pdf, name='liste_responsables_coordonnateurs_pdf'),

    # ✅ Nouvelle route ajoutée pour le tableau de statistiques des contrôleurs
    path('controleurs-cnss/', tableau_controleurs_cnss, name='tableau_controleurs_cnss'),
    path('controleurs/pdf/', liste_controleurs_pdf, name='liste_controleurs_pdf'),
    path('employes/cadres-direction/pdf/', liste_cadres_direction_pdf, name='liste_cadres_direction_pdf'),
    path('employes/retraitables/pdf/', liste_retraitables_pdf, name='liste_retraitables_pdf'),
    path('employes/', views.liste_employes, name='liste_employes'),
    path('logout/', logout_view, name='logout'),
    path('licencies/pdf/', views_pdf_weasyprint.liste_licencies_pdf, name='liste_licencies_pdf'),
    path('employes/disponibilites/pdf/', views_pdf_weasyprint.liste_disponibilite_pdf, name='liste_disponibilite_pdf'),
    path('retraites/pdf/', liste_retraites_pdf, name='liste_retraites_pdf'),
    path('decedes/pdf/', liste_decedes_pdf, name='liste_decedes_pdf'),
    path('detachement/pdf/', liste_detachement_pdf, name='liste_detachement_pdf'),
    path('demissionnaires/pdf/', liste_demissionnaires_pdf, name='liste_demissionnaires_pdf'),
    path('decedes/pdf/', views_pdf_weasyprint.liste_decedes_pdf, name='liste_decedes_pdf'),
    path("employes/demissionnaires/pdf/", liste_demissionnaires_pdf, name="liste_demissionnaires_pdf"),
    path('employes/detachement/pdf/', liste_detachement_pdf, name='liste_detachement_pdf'),

]
from . import urls_actifs  # ✅ Import des urls spécifiques aux actifs

urlpatterns += urls_actifs.urlpatterns  # ✅ Ajout des routes
