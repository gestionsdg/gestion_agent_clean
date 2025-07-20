from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse
from django.shortcuts import redirect
from django.contrib.auth import views as auth_views

# ✅ Correction ici : redirection avec import local
def redirection_accueil(request):
    from personnel.views_dashboard import tableau_de_bord
    if request.user.is_authenticated:
        return redirect('dashboard')
    else:
        return redirect('login')

urlpatterns = [
    path('', redirection_accueil, name='redirection_accueil'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='custom_login'),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),

    path('dashboard/', lambda request: __import__('personnel.views_dashboard').views_dashboard.tableau_de_bord(request), name='dashboard'),
    path('employes/', lambda request: __import__('personnel.views').views.liste_employes(request), name='liste_employes'),
    path('employes/ajouter/', lambda request: __import__('personnel.views').views.ajouter_employe(request), name='ajouter_employe'),

    path('test/', lambda request: HttpResponse("OK"), name='test'),

    path('personnel/', lambda request: __import__('personnel.views').views.accueil(request), name='personnel_accueil'),
    path('personnel/actifs/', include('personnel.urls_actifs')),
    path('export/', include('personnel.urls_export')),
    path('pdf/', include('personnel.urls_pdf')),
    path('filtre/', include('personnel.urls_filtrage')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
