from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve

from personnel import views  # ✅ Ajoutez cette ligne !
from personnel.views_dashboard import tableau_de_bord
from django.contrib.auth import views as auth_views
from personnel.views import accueil

urlpatterns = [
    # Accueil
    path('', accueil, name='accueil'),

    # Administration Django
    path('admin/', admin.site.urls),

    # Connexion personnalisée
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='custom_login'),

    # Tableau de bord
    path('dashboard/', tableau_de_bord, name='dashboard'),

    # Inclusion des URLs de l'application personnel
    path('employes/', views.liste_employes, name='liste_employes')
]

# Fichiers médias (pour DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Accès direct aux fichiers médias
urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

# Fichiers statiques (en production)
if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
