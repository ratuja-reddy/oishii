# oishii/oishii/settings.py
import os
from pathlib import Path
from urllib.parse import urlparse

import dj_database_url

# --------------------------------------------------------------------------------------
# Core
# --------------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY
SECRET_KEY = os.getenv("SECRET_KEY", "dev-only-not-secure")
DEBUG = os.getenv("DEBUG", "0") in {"1", "true", "True", "yes", "on"}

# Comma-separated, e.g. "yourdomain.com,www.yourdomain.com,app.onrender.com"
ALLOWED_HOSTS = [h for h in os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",") if h]

# If you’re terminating TLS at a proxy (Render/Railway/DO), pass proto header through:
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

# --------------------------------------------------------------------------------------
# Applications
# --------------------------------------------------------------------------------------
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "django_htmx",
    "storages",  # safe even if USE_S3=0

    # Local apps
    "social",
    "places",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",  # must be before CommonMiddleware
    "django_htmx.middleware.HtmxMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "oishii.urls"

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

WSGI_APPLICATION = "oishii.wsgi.application"

# --------------------------------------------------------------------------------------
# Database: SQLite for local, Postgres in prod
# --------------------------------------------------------------------------------------
DEFAULT_SQLITE_URL = f"sqlite:///{BASE_DIR / 'db.sqlite3'}"
DB_URL = os.getenv("DATABASE_URL", DEFAULT_SQLITE_URL)

scheme = urlparse(DB_URL).scheme
IS_POSTGRES = scheme in ("postgres", "postgresql")

DATABASES = {
    "default": dj_database_url.config(
        default=DB_URL,
        conn_max_age=600,                      # good for Postgres; harmless for SQLite
        ssl_require=IS_POSTGRES and not DEBUG, # SSL in prod Postgres only
    )
}

# --------------------------------------------------------------------------------------
# I18N / TZ
# --------------------------------------------------------------------------------------
LANGUAGE_CODE = "en-gb"
TIME_ZONE = "Europe/London"
USE_I18N = True
USE_TZ = True

# --------------------------------------------------------------------------------------
# Static files (served by WhiteNoise)
# --------------------------------------------------------------------------------------
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
candidate_static = BASE_DIR / "static"
if candidate_static.exists():
    STATICFILES_DIRS = [candidate_static]

# Always include a default storage; override to S3 below when USE_S3=1
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    "default": {
        "BACKEND": "django.core.files.storage.FileSystemStorage",
    },
}

# --------------------------------------------------------------------------------------
# Media: Cloudflare R2 (S3-compatible) or local FS
# --------------------------------------------------------------------------------------
USE_S3 = os.getenv("USE_S3", "0") in {"1", "true", "True", "yes", "on"}
MEDIA_ROOT = BASE_DIR / "media"

# Optional env override (recommended): e.g. https://pub-XXXX.r2.dev/ or https://media.myoishii.app/
ENV_MEDIA_URL = os.getenv("MEDIA_URL")

if ENV_MEDIA_URL:
    MEDIA_URL = ENV_MEDIA_URL if ENV_MEDIA_URL.endswith("/") else ENV_MEDIA_URL + "/"
else:
    MEDIA_URL = "/media/"

if USE_S3:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    # R2 endpoint like: https://<accountid>.r2.cloudflarestorage.com
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "auto")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "virtual"  # works well with R2/CDN

    # Public objects; no per-object ACLs; no signed querystrings for public media
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {"CacheControl": "max-age=31536000, public"}

    # Use S3 for default storage when enabled
    STORAGES["default"] = {"BACKEND": "storages.backends.s3boto3.S3Boto3Storage"}

    # If MEDIA_URL wasn't set explicitly, fall back to endpoint/bucket path
    if not ENV_MEDIA_URL:
        MEDIA_URL = (
            f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
            if AWS_S3_ENDPOINT_URL else "/media/"
        )

# --------------------------------------------------------------------------------------
# Security (enable fully in prod)
# --------------------------------------------------------------------------------------
if not DEBUG:
    CSRF_COOKIE_SECURE = True
    SESSION_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = int(os.getenv("SECURE_HSTS_SECONDS", "31536000"))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Trust your domains for CSRF if behind a proxy/CDN
_csrf_origins = os.getenv("CSRF_TRUSTED_ORIGINS")
if _csrf_origins:
    CSRF_TRUSTED_ORIGINS = [o for o in _csrf_origins.split(",") if o]

# --------------------------------------------------------------------------------------
# Logging to stdout/stderr (12-factor friendly)
# --------------------------------------------------------------------------------------
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {"console": {"class": "logging.StreamHandler"}},
    "root": {"handlers": ["console"], "level": os.getenv("LOG_LEVEL", "INFO")},
}

# --------------------------------------------------------------------------------------
# Default primary key type
# --------------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
