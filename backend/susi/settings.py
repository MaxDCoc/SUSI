import os
from pathlib import Path

import dj_database_url
from django.core.exceptions import ImproperlyConfigured

from .despliegue import encabezado_proxy_ssl, hosts_de_render, opciones_de_base, storages_desde_entorno

BASE_DIR = Path(__file__).resolve().parent.parent


def _env_list(nombre: str, por_defecto: str) -> list[str]:
    return [v.strip() for v in os.environ.get(nombre, por_defecto).split(",") if v.strip()]


DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"

SECRET_KEY = os.environ.get("DJANGO_SECRET_KEY", "")
if not SECRET_KEY:
    if not DEBUG:
        raise ImproperlyConfigured("DJANGO_SECRET_KEY es obligatoria cuando DJANGO_DEBUG=0")
    SECRET_KEY = "solo-para-desarrollo-no-usar-en-produccion"

_hosts_render, _origenes_render = hosts_de_render(os.environ)
ALLOWED_HOSTS = _env_list("DJANGO_ALLOWED_HOSTS", "localhost,127.0.0.1") + _hosts_render
# 5173 = servidor de Vite en desarrollo (el proxy conserva el header Origin).
CSRF_TRUSTED_ORIGINS = (
    _env_list("DJANGO_CSRF_TRUSTED_ORIGINS", "http://localhost:8000,http://localhost:5173") + _origenes_render
)
SESSION_COOKIE_SECURE = CSRF_COOKIE_SECURE = os.environ.get("DJANGO_SECURE_COOKIES", "0") == "1"
# Detrás de un proxy que termina HTTPS (Render): Django debe saber que la request original era segura.
SECURE_PROXY_SSL_HEADER = encabezado_proxy_ssl(os.environ)

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "simple_history",
    "guardian",
    "catalog",
    "accounts",
    "indicators",
    "evidence",
    "dashboard",
    "greenops",
]

MIDDLEWARE = [
    # Primero: así mide también la respuesta ya comprimida por GZip.
    "greenops.middleware.GreenOpsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.middleware.gzip.GZipMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "simple_history.middleware.HistoryRequestMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "susi.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "susi.wsgi.application"

if os.environ.get("DATABASE_URL"):
    DATABASES = {"default": dj_database_url.parse(os.environ["DATABASE_URL"], conn_max_age=60)}
    DATABASES["default"]["OPTIONS"] = {**DATABASES["default"].get("OPTIONS", {}), **opciones_de_base(os.environ)}
else:
    DATABASES = {"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": BASE_DIR / "db.sqlite3"}}

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "es-ar"
TIME_ZONE = "America/Argentina/Buenos_Aires"
USE_I18N = True
USE_TZ = True

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = Path(os.environ.get("SUSI_MEDIA_ROOT", BASE_DIR / "media"))
MEDIA_URL = "/media/"

# Archivos de evidencia: disco local, o un bucket S3 privado (Supabase Storage) si hay variables SUSI_S3_*.
STORAGES = storages_desde_entorno(os.environ)

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "guardian.backends.ObjectPermissionBackend",
]
ANONYMOUS_USER_NAME = None  # no se usa el usuario anónimo de guardian

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": ["rest_framework.authentication.SessionAuthentication"],
    "DEFAULT_PERMISSION_CLASSES": ["rest_framework.permissions.IsAuthenticated"],
    "DEFAULT_RENDERER_CLASSES": ["rest_framework.renderers.JSONRenderer"],
    "DEFAULT_PAGINATION_CLASS": "susi.pagination.PaginacionEstandar",
    "PAGE_SIZE": 20,
}

GREENOPS_ENABLED = os.environ.get("SUSI_GREENOPS", "1") == "1"

# Build de React: lo sirve la propia app (assets con WhiteNoise, index.html con la vista `spa`).
FRONTEND_DIST = Path(os.environ.get("SUSI_FRONTEND_DIST", BASE_DIR / "frontend_dist"))
if FRONTEND_DIST.is_dir():
    WHITENOISE_ROOT = FRONTEND_DIST
