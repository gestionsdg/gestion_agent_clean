# gestion_agent/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.static import serve as media_serve
from django.views.generic import RedirectView

# Vues globales utiles
from personnel.views import health
from personnel.views_dashboard import tableau_de_bord  # dashboard principal

# Chemin d'admin configurable par settings.ADMIN_URL ; on assure le slash final
ADMIN_PATH = getattr(settings, "ADMIN_URL", "supervision/")
if not ADMIN_PATH.endswith("/"):
    ADMIN_PATH += "/"

urlpatterns = [
    # ===== Racine du site : redirection automatique vers /connexion/ =====
    path("", RedirectView.as_view(pattern_name="connexion", permanent=False), name="root"),

    # ===== Tableau de bord principal =====
    # /dashboard/ -> vue tableau_de_bord (nom simple: "dashboard")
    path("dashboard/", tableau_de_bord, name="dashboard"),

    # ===== Alias globaux utilisés (dashboard, boutons, etc.) =====

    # Carte "Total Agents" : {% url 'liste_total_agents' %}
    path(
        "liste-total-agents/",
        RedirectView.as_view(pattern_name="personnel:liste_total_agents", permanent=False),
        name="liste_total_agents",
    ),

    # Bouton "➡ Accéder à la liste des agents" : {% url 'liste_employes' %}
    path(
        "liste-employes/",
        RedirectView.as_view(pattern_name="personnel:liste_employes", permanent=False),
        name="liste_employes",
    ),

    # Carte "Agents Actifs" : {% url 'liste_actifs_par_entite' %}
    path(
        "liste-actifs-par-entite/",
        RedirectView.as_view(pattern_name="personnel:liste_actifs_par_entite", permanent=False),
        name="liste_actifs_par_entite",
    ),

    # Carte "Retraités" : {% url 'liste_retraites_pdf' %}
    path(
        "liste-retraites-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_retraites_pdf", permanent=False),
        name="liste_retraites_pdf",
    ),

    # Carte "Décédés" : {% url 'liste_decedes_pdf' %}
    path(
        "liste-decedes-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_decedes_pdf", permanent=False),
        name="liste_decedes_pdf",
    ),

    # Carte "Licenciés (actuels)" : {% url 'liste_licencies_pdf' %}
    path(
        "liste-licencies-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_licencies_pdf", permanent=False),
        name="liste_licencies_pdf",
    ),

    # Carte "Disponibilités (situation actuelle)" : {% url 'liste_disponibilite_pdf' %}
    path(
        "liste-disponibilite-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_disponibilite_pdf", permanent=False),
        name="liste_disponibilite_pdf",
    ),

    # Carte "Agents ayant été licenciés (historique)" :
    # {% url 'liste_agents_ayant_ete_licencies_pdf' %}
    path(
        "liste-agents-ayant-ete-licencies-pdf/",
        RedirectView.as_view(
            pattern_name="personnel:liste_agents_ayant_ete_licencies_pdf",
            permanent=False,
        ),
        name="liste_agents_ayant_ete_licencies_pdf",
    ),

    # Carte "Démissionnaires" : {% url 'liste_demissionnaires_pdf' %}
    path(
        "liste-demissionnaires-pdf/",
        RedirectView.as_view(
            pattern_name="personnel:liste_demissionnaires_pdf",
            permanent=False,
        ),
        name="liste_demissionnaires_pdf",
    ),

    # Carte "Agents en détachement" : {% url 'liste_detachement_pdf' %}
    path(
        "liste-detachement-pdf/",
        RedirectView.as_view(
            pattern_name="personnel:liste_detachement_pdf",
            permanent=False,
        ),
        name="liste_detachement_pdf",
    ),

    # Carte "Agents mis en disponibilité" :
    # {% url 'liste_agents_mis_en_disponibilite_pdf' %}
    path(
        "liste-agents-mis-en-disponibilite-pdf/",
        RedirectView.as_view(
            pattern_name="personnel:liste_agents_mis_en_disponibilite_pdf",
            permanent=False,
        ),
        name="liste_agents_mis_en_disponibilite_pdf",
    ),

    # Autres PDF utiles déjà présents
    path(
        "liste-retraitables-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_retraitables_pdf", permanent=False),
        name="liste_retraitables_pdf",
    ),
    path(
        "liste-cadres-direction-pdf/",
        RedirectView.as_view(pattern_name="personnel:liste_cadres_direction_pdf", permanent=False),
        name="liste_cadres_direction_pdf",
    ),

    # ===== Authentification =====
    path(
        "connexion/",
        auth_views.LoginView.as_view(
            template_name="registration/login.html"
        ),
        name="connexion",
    ),
    path("deconnexion/", auth_views.LogoutView.as_view(), name="deconnexion"),

    # Alias anciens (compatibilité)
    path("login/", RedirectView.as_view(pattern_name="connexion", permanent=False)),
    path("logout/", RedirectView.as_view(pattern_name="deconnexion", permanent=False)),

    # ===== Admin =====
    path(ADMIN_PATH, admin.site.urls),

    # ===== Routes de l’app Personnel =====
    path("personnel/", include(("personnel.urls", "personnel"), namespace="personnel")),

    # ===== Healthcheck =====
    path("__health__", health, name="__health__"),
]

# ===== Compat locale pour /admin/ quand DEBUG=True =====
if settings.DEBUG:
    admin_url_abs = ADMIN_PATH if ADMIN_PATH.startswith("/") else "/" + ADMIN_PATH
    urlpatterns.insert(
        0, path("admin/", RedirectView.as_view(url=admin_url_abs, permanent=False))
    )

# ===== Gestion des médias =====
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    urlpatterns += [
        re_path(
            r"^media/(?P<path>.*)$",
            media_serve,
            {"document_root": settings.MEDIA_ROOT},
            name="media",
        ),
    ]
