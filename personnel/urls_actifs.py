from django.urls import path
from .views_actifs import liste_actifs_cnss, liste_actifs_cnss_pdf

urlpatterns = [
    path('employes/actifs-cnss/', liste_actifs_cnss, name='liste_actifs_cnss'),
    path('employes/actifs-cnss/pdf/', liste_actifs_cnss_pdf, name='liste_actifs_cnss_pdf'),
]
