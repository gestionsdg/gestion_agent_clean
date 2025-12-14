import os
from pathlib import Path
from decouple import config
# import dj_database_url  # Plus nécessaire pour le moment en local

# Répertoire de base
BASE_DIR = Path(__file__).resolve().parent.parent

# Clé secrète (gérée via variables d’environnement en production)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-votre_clé_secrète_à_remplacer')

# Mode DEBUG
DEBUG = config('DEBUG', default=True, cast=bool)

# Hôtes autorisés
ALLOWED_HOSTS = ['gestion-agent.onrender.com', '127.0.0.1', 'localhost']

# ================================
# 🌍 LANGUE & FUSEAU HORAIRE
# ================================
LANGUAGE_CODE = 'fr'                 # Interface Django en français
TIME_ZONE = 'Africa/Kinshasa'        # Ton fuseau horaire
USE_I18N = True
USE_TZ = True

# Applications installées
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # vos apps
    'personnel',
    'widget_tweaks',
]

# Middleware
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'gestion_agent.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'gestion_agent.wsgi.application'

# ==========================
# Base de données (LOCAL)
# ==========================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# Fichiers médias
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Paramètres de sécurité (prod uniquement)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_SSL_REDIRECT = True

LOGIN_REDIRECT_URL = '/dashboard/'
LOGOUT_REDIRECT_URL = '/connexion/'
