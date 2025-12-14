# personnel/urls_export.py
from django.urls import path
from . import views_export as v

urlpatterns = [
    # Listes HTML (si tu les utilises encore)
    path('liste_actifs_par_entite/', v.liste_actifs_par_entite, name='liste_actifs_par_entite'),
    path('liste_decedes/', v.liste_decedes, name='liste_decedes'),
    path('liste_retraites/', v.liste_retraites, name='liste_retraites'),
    path('liste_demis/', v.liste_demis, name='liste_demis'),
    path('liste_detaches/', v.liste_detaches, name='liste_detaches'),
    path('liste_licencies/', v.liste_licencies, name='liste_licencies'),
    path('liste_disponibilites/', v.liste_disponibilites, name='liste_disponibilites'),
    path('liste_responsables_par_entite/', v.liste_responsables_par_entite, name='liste_responsables_par_entite'),

    # Contrôleurs (HTML + PDF)
    path('liste_controleurs/', v.liste_controleurs, name='liste_controleurs'),
    path('liste_controleurs/pdf/', v.liste_controleurs_pdf, name='liste_controleurs_pdf'),

    # Effectif par entité (HTML)
    path('liste_effectif_par_entite/', v.liste_effectif_par_entite, name='liste_effectif_par_entite'),

    # (optionnel) totaux HTML si utilisés
    path('total_agents/', v.total_agents, name='total_agents'),
    path('agents_actifs/', v.agents_actifs, name='agents_actifs'),
]
