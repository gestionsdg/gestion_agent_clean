from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# ✅ Vue de redirection d'accueil
def redirection_accueil(request):
    if request.user.is_authenticated:
        return redirect('dashboard')  # Redirige vers tableau de bord si connecté
    else:
        return redirect('login')  # Sinon vers login

# ✅ Vos vues personnalisées
from personnel.views import accueil, liste_employes, ajouter_employe
from personnel.views_dashboard import tableau_de_bord

urlpatterns = [
    path('', redirection_accueil, name='redirection_accueil'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='custom_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('dashboard/', tableau_de_bord, name='dashboard'),
    path('employes/', liste_employes, name='liste_employes'),
    path('employes/ajouter/', ajouter_employe, name='ajouter_employe'),

    path('test/', lambda request: HttpResponse("OK"), name='test'),

    path('personnel/', accueil, name='personnel_accueil'),
    path('personnel/actifs/', include('personnel.urls_actifs')),
    path('export/', include('personnel.urls_export')),
    path('pdf/', include('personnel.urls_pdf')),
    path('filtre/', include('personnel.urls_filtrage')),
]

# ✅ Fichiers médias en développement
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
