"""Project settings for the APL injury risk and rotation service."""
from pathlib import Path
import os

from django.core.management.utils import get_random_secret_key


BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY") or get_random_secret_key()
DEBUG = os.environ.get("DJANGO_DEBUG", "False").lower() == "true"

ALLOWED_HOSTS = [
    host.strip()
    for host in os.environ.get(
        "DJANGO_ALLOWED_HOSTS",
        "127.0.0.1,localhost,.pythonanywhere.com",
    ).split(",")
    if host.strip()
]


INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rotations",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "apl_risk.urls"

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
            ],
        },
    },
]

WSGI_APPLICATION = "apl_risk.wsgi.application"


DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


LANGUAGE_CODE = "ru-ru"
TIME_ZONE = "Asia/Yekaterinburg"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = []

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

FPL_API_URL = os.environ.get(
    "FPL_API_URL",
    "https://fantasy.premierleague.com/api/bootstrap-static/",
)
FPL_SYNC_INTERVAL_HOURS = int(os.environ.get("FPL_SYNC_INTERVAL_HOURS", "12"))
FPL_SYNC_LOCK_SECONDS = int(os.environ.get("FPL_SYNC_LOCK_SECONDS", "600"))
FPL_API_TIMEOUT = int(os.environ.get("FPL_API_TIMEOUT", "30"))

TRANSFERMARKT_SEASON_ID = int(os.environ.get("TRANSFERMARKT_SEASON_ID", "2024"))
TRANSFERMARKT_REQUEST_DELAY = float(os.environ.get("TRANSFERMARKT_REQUEST_DELAY", "0.35"))
TRANSFERMARKT_TIMEOUT = int(os.environ.get("TRANSFERMARKT_TIMEOUT", "30"))
TRANSFERMARKT_AUTO_BATCH_SIZE = int(os.environ.get("TRANSFERMARKT_AUTO_BATCH_SIZE", "0"))
TRANSFERMARKT_SYNC_BATCH_SIZE = int(os.environ.get("TRANSFERMARKT_SYNC_BATCH_SIZE", "9999"))
TRANSFERMARKT_SYNC_LOCK_SECONDS = int(os.environ.get("TRANSFERMARKT_SYNC_LOCK_SECONDS", "3600"))

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
        "LOCATION": "apl-injury-risk",
    }
}

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "dashboard"
LOGOUT_REDIRECT_URL = "dashboard"
