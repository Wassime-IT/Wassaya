# wassaya_project/settings.py
from pathlib import Path
import os

BASE_DIR = Path(__file__).resolve().parent.parent

# =======================
# Sécurité / environnement
# =======================
# En prod: mets SECRET_KEY en variable d'environnement
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")

# ✅ IMPORTANT : DEBUG par défaut = True en local
# Tu peux forcer DEBUG=0 en prod
DEBUG = os.getenv("DEBUG", "1") == "1"

# Hosts
ALLOWED_HOSTS = (
    os.getenv("ALLOWED_HOSTS", "").split(",")
    if os.getenv("ALLOWED_HOSTS")
    else ["127.0.0.1", "localhost"]
)
if "*" in ALLOWED_HOSTS:
    # tu peux laisser ["*"] si tu veux, mais c'est moins safe
    pass

# =======================
# Applications installées
# =======================
INSTALLED_APPS = [
    # Django core
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "corsheaders",

    # Local apps
    "wassaya_users",
    "wassaya_clinic",
    "wassaya_rdv",
    "webui",
]

# =======================
# Middlewares
# =======================
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",  # doit être avant CommonMiddleware
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# =======================
# URL / WSGI
# =======================
ROOT_URLCONF = "wassaya_project.urls"
WSGI_APPLICATION = "wassaya_project.wsgi.application"

# =======================
# Templates (admin)
# =======================
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",  # requis pour admin
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# =======================
# Database (SQLite en dev)
# =======================
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# (Option docker/postgres) — si tu veux activer plus tard, décommente:
"""
if os.getenv("DB_HOST"):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.getenv("DB_NAME", "wassaya"),
            "USER": os.getenv("DB_USER", "wassaya"),
            "PASSWORD": os.getenv("DB_PASSWORD", "wassaya"),
            "HOST": os.getenv("DB_HOST", "db"),
            "PORT": os.getenv("DB_PORT", "5432"),
        }
    }
"""

# =======================
# User custom
# =======================
AUTH_USER_MODEL = "wassaya_users.User"

# =======================
# DRF + JWT
# =======================
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
}

# =======================
# CORS (dev)
# =======================
CORS_ALLOW_ALL_ORIGINS = True

# =======================
# Internationalisation
# =======================
LANGUAGE_CODE = "fr-fr"
TIME_ZONE = "Africa/Casablanca"
USE_I18N = True
USE_TZ = True

# =======================
# Static files (ADMIN CSS FIX ✅)
# =======================
# ✅ IMPORTANT: slash obligatoire
STATIC_URL = "/static/"
STATICFILES_DIRS = [BASE_DIR / "webui" / "static"]

# Optionnel (utile plus tard pour prod / collectstatic)
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# =======================
# Paramètres spécifiques à Wassaya
# =======================
SITE_URL = os.getenv("SITE_URL", "http://127.0.0.1:8000").rstrip("/")

# =======================
# EMAIL (Mailpit en local)
# =======================
EMAIL_BACKEND = os.getenv("EMAIL_BACKEND", "django.core.mail.backends.smtp.EmailBackend")
EMAIL_HOST = os.getenv("EMAIL_HOST", "127.0.0.1")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "1026"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "0") in ("1", "true", "True")
EMAIL_USE_SSL = False

DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "Wassaya <no-reply@wassaya.local>")

# ===== END =====
# EXPL: Configuration principale de Django pour le projet Wassaya, incluant sécurité, applications, base de données, authentification, CORS, internationalisation, fichiers statiques et paramètres email.