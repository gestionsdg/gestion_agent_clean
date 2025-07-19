from django.urls import path
from . import views_export

urlpatterns = [
    path('actifs/', views_export.liste_actifs_par_entite, name='liste_actifs_par_entite'),
    path('decedes/', views_export.liste_decedes, name='liste_decedes'),
    path('retraites/', views_export.liste_retraites, name='liste_retraites'),
    path('demis/', views_export.liste_demis, name='liste_demis'),
    path('detaches/', views_export.liste_detaches, name='liste_detaches'),
    path('licencies/', views_export.liste_licencies, name='liste_licencies'),
    path('disponibilites/', views_export.liste_disponibilites, name='liste_disponibilites'),
    path('responsables/', views_export.liste_responsables_par_entite, name='liste_responsables_par_entite'),
    path('controleurs/', views_export.liste_controleurs, name='liste_controleurs'),
    path('export_excel/', views_export.export_employes_excel, name='export_employes_excel'),
    path('export_excel_complet/', views_export.export_employes_excel_complet, name='export_employes_excel_complet'),
]
