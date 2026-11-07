import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

# ==========================================
# M-PESA DARAJA CONFIGURATION
# ==========================================

MPESA_ENVIRONMENT = os.getenv(
    "MPESA_ENVIRONMENT",
    "sandbox"
)

MPESA_CONSUMER_KEY = os.getenv(
    "MPESA_CONSUMER_KEY",
    ""
)

MPESA_CONSUMER_SECRET = os.getenv(
    "MPESA_CONSUMER_SECRET",
    ""
)

MPESA_SHORTCODE = os.getenv(
    "MPESA_SHORTCODE",
    ""
)

MPESA_PASSKEY = os.getenv(
    "MPESA_PASSKEY",
    ""
)

MPESA_CALLBACK_URL = os.getenv(
    "MPESA_CALLBACK_URL",
    ""
)

SECRET_KEY = os.environ["DJANGO_SECRET_KEY"]

# Development settings
DEBUG = True

ALLOWED_HOSTS = [
    "127.0.0.1",
    "localhost",
    "distinct-width-timid.ngrok-free.dev/mpesa/callback/",
]
CSRF_TRUSTED_ORIGINS = [
    "https://distinct-width-timid.ngrok-free.dev/mpesa/callback/",
]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "smart_rental.rental",
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

ROOT_URLCONF = "smart_rental.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [
            BASE_DIR / "smart_rental" / "rental" / "templates"
        ],
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

WSGI_APPLICATION = "smart_rental.wsgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

AUTH_PASSWORD_VALIDATORS = []

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Nairobi"

USE_I18N = True

USE_TZ = True

# Static files configuration

STATIC_URL = "/static/"

STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"