import os
from pathlib import Path
from decouple import config
import dj_database_url

# 🔹 Répertoire de base
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔹 Clé secrète (gérée via variables d’environnement en production)
SECRET_KEY = config('SECRET_KEY', default='django-insecure-votre_clé_secrète_à_remplacer')

# 🔹 Mode DEBUG (True en local, False en production Render)
DEBUG = config('DEBUG', default=True, cast=bool)

# 🔹 Hôtes autorisés (Render les définit via ALLOWED_HOSTS)
ALLOWED_HOSTS = config('ALLOWED_HOSTS', default='').split(',') if not DEBUG else []

# 🔹 Applications installées
INSTALLED_APPS = [
    'personnel',  # Votre application RH
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'widget_tweaks',
]

# 🔹 Middleware (ajout de WhiteNoise pour fichiers statiques en prod)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # AJOUT POUR RENDER
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# 🔹 Fichier urls.py principal
ROOT_URLCONF = 'gestion_agent.urls'

# 🔹 Templates (dossier "templates")
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],  # Dossier templates global
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

# 🔹 Application WSGI
WSGI_APPLICATION = 'gestion_agent.wsgi.application'

# 🔹 Base de données : SQLite en local, PostgreSQL sur Render
if DEBUG:
    # Mode local : SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Mode production : PostgreSQL via Render
    DATABASES = {
        'default': dj_database_url.config(default=config('DATABASE_URL'))
    }

# 🔹 Validation des mots de passe
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]

# 🔹 Langue et fuseau horaire
LANGUAGE_CODE = 'fr-fr'
TIME_ZONE = 'Africa/Kinshasa'
USE_I18N = True
USE_TZ = True

# 🔹 Fichiers statiques
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / 'static']
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Pour production

# WhiteNoise : optimisation des fichiers statiques en prod
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# 🔹 Fichiers médias
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 🔹 Type de clé auto par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 🔹 Redirection après connexion réussie
LOGIN_URL = '/connexion/'
LOGIN_REDIRECT_URL = '/dashboard/'
