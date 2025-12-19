import os
from pathlib import Path
from decouple import config, Csv
import dj_database_url
from urllib.parse import urlparse
from django.core.exceptions import ImproperlyConfigured

# Répertoire de base
BASE_DIR = Path(__file__).resolve().parent.parent

# ===== Langue & fuseau (Admin + site en FR) =====
LANGUAGE_CODE = "fr"
TIME_ZONE = "Africa/Kinshasa"
USE_I18N = True
USE_TZ = True

LANGUAGES = [
    ("fr", "Français"),
    ("en", "English"),
]

LOCALE_PATHS = [BASE_DIR / "locale"]

# DEBUG (True en local, False en production)
DEBUG = config("DEBUG", default=False, cast=bool)

# Clé secrète : lue depuis l'environnement (ne pas versionner de vraie clé)
# Sur Render, mets DJANGO_SECRET_KEY dans les variables d'environnement
SECRET_KEY = config("DJANGO_SECRET_KEY", default=config("SECRET_KEY", default=""))

if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured(
            "SECRET_KEY manquant : définis DJANGO_SECRET_KEY (ou SECRET_KEY) dans l'environnement."
        )
    SECRET_KEY = "django-insecure-dev-only-change-me"

# Hôtes autorisés (séparés par virgules dans Render)
ALLOWED_HOSTS = config(
    "ALLOWED_HOSTS",
    default="gestion-agent.onrender.com,gestion-agent-clean.onrender.com,.onrender.com,127.0.0.1,localhost,testserver",
    cast=Csv(),
)

# CSRF (séparés par virgules dans Render)
# Note : Django accepte les wildcards sous forme https://*.domaine
CSRF_TRUSTED_ORIGINS = config(
    "CSRF_TRUSTED_ORIGINS",
    default="https://gestion-agent.onrender.com,https://gestion-agent-clean.onrender.com,https://*.onrender.com",
    cast=Csv(),
)

# Chemin d’admin configurable (avec / final)
ADMIN_URL = config("ADMIN_URL", default="supervision/")
if not ADMIN_URL.endswith("/"):
    ADMIN_URL += "/"

# Render/Proxy : faire confiance au header proxy (HTTPS) + host
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
USE_X_FORWARDED_HOST = True

# === Limite par défaut pour les exports PDF (contrôle mémoire/timeout en prod) ===
PDF_MAX_ROWS = int(os.getenv("PDF_MAX_ROWS", "1500"))

# Applications installées
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # apps projet
    "personnel",
    "widget_tweaks",

    # Sécurité : Content Security Policy
    "csp",

    # Outils développeur
    "django_extensions",
]

# Middleware
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",

    # Forcer l’auth sur tout le site (sauf URLs exemptées)
    "personnel.middleware.LoginRequiredMiddleware",

    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",

    # CSP
    "csp.middleware.CSPMiddleware",
]

ROOT_URLCONF = "gestion_agent.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "django.template.context_processors.i18n",

                # Logo base64 partout
                "personnel.context_processors.logo_b64",
            ],
        },
    },
]

WSGI_APPLICATION = "gestion_agent.wsgi.application"

# Base de données
_default_db_url = config("DATABASE_URL", default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}")
_db_host = (urlparse(_default_db_url).hostname or "")

# SSL DB : si URL externe Render (*.render.com) et prod => ssl_require True
_ssl_require = (".render.com" in _db_host) and not DEBUG

DATABASES = {
    "default": dj_database_url.parse(
        _default_db_url,
        conn_max_age=600,
        ssl_require=_ssl_require,
    )
}

# Fichiers statiques
STATIC_URL = "/static/"

# Évite crash si le dossier /static n'existe pas
_static_dir = BASE_DIR / "static"
STATICFILES_DIRS = [_static_dir] if _static_dir.exists() else []

STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Fichiers médias (si utilisés)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Champ auto par défaut
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sécurité prod
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True

    # HSTS (active après validation HTTPS OK)
    SECURE_HSTS_SECONDS = 60 * 60 * 24 * 30
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True

    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
    SECURE_CROSS_ORIGIN_OPENER_POLICY = "same-origin"
    X_FRAME_OPTIONS = "DENY"

# CSP (django-csp >= 4.0)
CSP_POLICY_DIRECTIVES = {
    "default-src": ("'self'",),
    "style-src": ("'self'", "'unsafe-inline'"),
    "script-src": ("'self'",),
    "img-src": ("'self'", "data:"),
    "font-src": ("'self'", "data:"),
}

# Auth redirects
LOGIN_URL = "connexion"
LOGIN_REDIRECT_URL = "personnel:dashboard"
LOGOUT_REDIRECT_URL = "connexion"

# LOGGING : erreurs vers stdout (Render capte les logs)
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": "ERROR"},
    "loggers": {
        "django": {"handlers": ["console"], "level": "ERROR", "propagate": True},
        "django.request": {"handlers": ["console"], "level": "ERROR", "propagate": False},
    },
}
