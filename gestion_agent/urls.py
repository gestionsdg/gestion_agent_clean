from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse

# Vues locales
from personnel.views import accueil, liste_employes, ajouter_employe
from personnel.views_dashboard import tableau_de_bord
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', accueil, name='accueil'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='custom_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('dashboard/', tableau_de_bord, name='dashboard'),
    path('employes/', liste_employes, name='liste_employes'),
    path('employes/ajouter/', ajouter_employe, name='ajouter_employe'),

    path('test/', lambda request: HttpResponse("OK"), name='test'),

    # ✅ Nouveau pour rendre /personnel/ accessible
    path('personnel/', accueil, name='personnel_accueil'),
    path('personnel/actifs/', include('personnel.urls_actifs')),

    path('export/', include('personnel.urls_export')),
    path('pdf/', include('personnel.urls_pdf')),
    path('filtre/', include('personnel.urls_filtrage')),
]
