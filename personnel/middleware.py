# personnel/middleware.py
from django.shortcuts import redirect
from django.urls import resolve, reverse, NoReverseMatch

# Préfixes (chemins) toujours publics : assets, healthchecks, etc.
EXEMPT_PREFIXES = (
    "/static/", "/media/", "/__health__", "/_health",
    "/favicon.ico", "/robots.txt",
)

# Noms de vues publics (avec ou sans namespace)
EXEMPT_VIEWNAMES = {
    "connexion",
    "logout", "deconnexion",  # selon ton projet
    "password_reset", "password_reset_done",
    "password_reset_confirm", "password_reset_complete",
    "admin:login",
    # Ajoute ici d’éventuelles vues publiques spécifiques (ex: webhook)
}

def _login_path_fallback():
    """Calcule le chemin de la page de connexion de façon sûre."""
    try:
        return reverse("connexion")
    except NoReverseMatch:
        # Chemin de secours si le nom 'connexion' n'existe pas
        return "/connexion/"

class LoginRequiredMiddleware:
    """
    Force la connexion sur TOUTES les pages, sauf URLs explicitement exemptées.
    À placer APRÈS AuthenticationMiddleware dans settings.MIDDLEWARE.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self._login_path = _login_path_fallback()

    def __call__(self, request):
        path = request.path

        # 0) Laisse passer les préfixes "techniques" (assets, health, favicon…)
        if path.startswith(EXEMPT_PREFIXES):
            return self.get_response(request)

        # 1) Laisse passer la page de connexion elle-même (par chemin)
        #    -> évite toute boucle en cas de problème de nom de route
        if path == self._login_path:
            return self.get_response(request)

        # 2) Si utilisateur déjà connecté -> OK
        if request.user.is_authenticated:
            return self.get_response(request)

        # 3) Pour les non connectés : vérifie si la vue ciblée est dans les exemptions
        viewname = ""
        try:
            match = resolve(path)
            # Exemple: "admin:login" ou "connexion"
            if match.url_name:
                viewname = f"{match.namespace + ':' if match.namespace else ''}{match.url_name}"
        except Exception:
            # Chemin non résolu (ex: URL inconnue) -> on force login
            return redirect(self._login_path)

        if viewname in EXEMPT_VIEWNAMES:
            return self.get_response(request)

        # 4) Tout le reste -> redirection vers login
        return redirect(self._login_path)
