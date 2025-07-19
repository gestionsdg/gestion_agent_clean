from django.urls import path
from . import views_pdf_weasyprint

urlpatterns = [
    path('fiche/<int:pk>/pdf/', views_pdf_weasyprint.fiche_employe_pdf, name='fiche_employe_pdf'),
    path('responsables-par-entite/pdf/', views_pdf_weasyprint.liste_responsables_par_entite_pdf, name='liste_responsables_par_entite_pdf'),
    path('controleurs/pdf/', views_pdf_weasyprint.liste_controleurs_pdf, name='liste_controleurs_pdf'),
    path('responsables-coordonnateurs/pdf/', views_pdf_weasyprint.liste_responsables_coordonnateurs_pdf, name='liste_responsables_coordonnateurs_pdf'),
    path('actifs-par-entite/pdf/', views_pdf_weasyprint.liste_actifs_par_entite_pdf, name='liste_actifs_par_entite_pdf'),
    path('cadres-direction/pdf/', views_pdf_weasyprint.liste_cadres_direction_pdf, name='liste_cadres_direction_pdf'),
    path('retraitables/pdf/', views_pdf_weasyprint.liste_retraitables_pdf, name='liste_retraitables_pdf'),
    path('detaches/pdf/', views_pdf_weasyprint.liste_detaches_pdf, name='liste_detaches_pdf'),
    path('licencies/pdf/', views_pdf_weasyprint.liste_licencies_pdf, name='liste_licencies_pdf'),
    path('disponibilites/pdf/', views_pdf_weasyprint.liste_disponibilite_pdf, name='liste_disponibilite_pdf'),
    path('retraites/pdf/', views_pdf_weasyprint.liste_retraites_pdf, name='liste_retraites_pdf'),
    path('detachement/pdf/', views_pdf_weasyprint.liste_detachement_pdf, name='liste_detachement_pdf'),
    path('demissionnaires/pdf/', views_pdf_weasyprint.liste_demissionnaires_pdf, name='liste_demissionnaires_pdf'),
    path('decedes/pdf/', views_pdf_weasyprint.liste_decedes_pdf, name='liste_decedes_pdf'),
]
