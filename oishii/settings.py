# oishii/oishii/settings.py
from pathlib import Path
import os
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
    "social",    # present in your repo; add others here if needed
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
# Database
# - Local: SQLite by default
# - Prod: set DATABASE_URL (Postgres on Render/Railway/DO)
# --------------------------------------------------------------------------------------
DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
        ssl_require=os.getenv("DB_SSL", "1") in {"1", "true", "True", "yes", "on"},
    )
}

# --------------------------------------------------------------------------------------
# Password validation
# --------------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

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
# Include your source static folder if you keep one:
candidate_static = BASE_DIR / "static"
if candidate_static.exists():
    STATICFILES_DIRS = [candidate_static]

# WhiteNoise hashed + compressed storage
STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
    # "default" is set below. If not using S3, Django's default FileSystemStorage is used.
}

# --------------------------------------------------------------------------------------
# Media: Cloudflare R2 (S3-compatible) or local FS
# - Flip on by setting USE_S3=1 and the R2 env vars.
# - To migrate to AWS S3 later: change keys/region and remove the endpoint (or set AWS endpoint).
# --------------------------------------------------------------------------------------
USE_S3 = os.getenv("USE_S3", "0") in {"1", "true", "True", "yes", "on"}
MEDIA_ROOT = BASE_DIR / "media"

# Optional env override (recommended): e.g. https://pub-XXXX.r2.dev/ or https://media.myoishii.app/
ENV_MEDIA_URL = os.getenv("MEDIA_URL")

if USE_S3:
    AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
    AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
    AWS_STORAGE_BUCKET_NAME = os.getenv("AWS_STORAGE_BUCKET_NAME")
    # R2 endpoint like: https://<accountid>.r2.cloudflarestorage.com
    AWS_S3_ENDPOINT_URL = os.getenv("AWS_S3_ENDPOINT_URL")
    AWS_S3_REGION_NAME = os.getenv("AWS_S3_REGION_NAME", "auto")
    AWS_S3_SIGNATURE_VERSION = "s3v4"
    AWS_S3_ADDRESSING_STYLE = "virtual"  # works well with R2/CDN

    # Public objects; don’t attach per-object ACLs; no signed querystrings for public media
    AWS_DEFAULT_ACL = None
    AWS_QUERYSTRING_AUTH = False
    AWS_S3_OBJECT_PARAMETERS = {
        "CacheControl": "max-age=31536000, public"
    }

    STORAGES["default"] = {
        "BACKEND": "storages.backends.s3boto3.S3Boto3Storage",
    }

    # MEDIA_URL precedence:
    # 1) If you set MEDIA_URL in env (Public Dev URL or custom domain), use that.
    # 2) Else, fall back to direct endpoint/bucket path.
    if ENV_MEDIA_URL:
        MEDIA_URL = ENV_MEDIA_URL if ENV_MEDIA_URL.endswith("/") else ENV_MEDIA_URL + "/"
    else:
        MEDIA_URL = (
            f"{AWS_S3_ENDPOINT_URL}/{AWS_STORAGE_BUCKET_NAME}/"
            if AWS_S3_ENDPOINT_URL else "/media/"
        )
else:
    # Local filesystem (dev). Allow env override but ensure trailing slash.
    if ENV_MEDIA_URL:
        MEDIA_URL = ENV_MEDIA_URL if ENV_MEDIA_URL.endswith("/") else ENV_MEDIA_URL + "/"
    else:
        MEDIA_URL = "/media/"

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
    # Optional: tighten referrer policy
    SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"

# Trust your domains for CSRF if behind a proxy/CDN
# Example: CSRF_TRUSTED_ORIGINS="https://yourdomain.com,https://www.yourdomain.com"
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
