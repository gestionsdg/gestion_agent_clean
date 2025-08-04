import os
from pathlib import Path

# 🔹 Répertoire de base
BASE_DIR = Path(__file__).resolve().parent.parent

# 🔹 Clé secrète (à sécuriser en production)
SECRET_KEY = 'django-insecure-votre_clé_secrète_à_remplacer'

# 🔹 Mode DEBUG activé pour développement local
DEBUG = True

# 🔹 Hôtes autorisés (aucun pour local)
ALLOWED_HOSTS = []

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

# 🔹 Middleware (par défaut)
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
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

# 🔹 Base de données SQLite pour local
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# 🔹 Validation des mots de passe (par défaut)
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

# 🔹 Fichiers médias (images, photos d'agents, etc.)
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# 🔹 Type de clé auto par défaut
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# 🔹 Redirection après connexion réussie
LOGIN_REDIRECT_URL = '/dashboard/'
