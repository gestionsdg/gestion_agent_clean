from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import HttpResponse

from personnel.views import accueil, liste_employes, ajouter_employe  # ✅ CORRIGÉ
from personnel.views_dashboard import tableau_de_bord
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', accueil, name='accueil'),
    path('admin/', admin.site.urls),
    path('login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('connexion/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='custom_login'),
    path('dashboard/', tableau_de_bord, name='dashboard'),

    path('employes/', liste_employes, name='liste_employes'),
    path('employes/ajouter/', ajouter_employe, name='ajouter_employe'),  # ✅ AJOUTÉ

    path('test/', lambda request: HttpResponse("OK"), name='test'),
]

# Fichiers médias (pour DEBUG = True)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += [
    re_path(r'^media/(?P<path>.*)$', serve, {'document_root': settings.MEDIA_ROOT}),
]

if not settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
