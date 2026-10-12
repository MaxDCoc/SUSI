"""Configuración que depende del entorno de despliegue (Render, Supabase, proxy HTTPS).

Son funciones puras sobre un diccionario de entorno para poder probarlas sin tocar `os.environ`.
"""

from django.core.exceptions import ImproperlyConfigured

ESTATICOS = {"BACKEND": "whitenoise.storage.CompressedStaticFilesStorage"}

# Variable de entorno -> opción de django-storages (S3 compatible: Supabase Storage, R2, MinIO...).
_VARIABLES_S3 = {
    "SUSI_S3_ENDPOINT_URL": "endpoint_url",
    "SUSI_S3_BUCKET": "bucket_name",
    "SUSI_S3_ACCESS_KEY": "access_key",
    "SUSI_S3_SECRET_KEY": "secret_key",
    "SUSI_S3_REGION": "region_name",
}


def storages_desde_entorno(env) -> dict:
    """STORAGES de Django: disco local, o un bucket S3 privado si hay variables SUSI_S3_*."""
    configuradas = [nombre for nombre in _VARIABLES_S3 if env.get(nombre)]
    if not configuradas:
        return {"default": {"BACKEND": "django.core.files.storage.FileSystemStorage"}, "staticfiles": ESTATICOS}

    faltantes = [nombre for nombre in _VARIABLES_S3 if not env.get(nombre)]
    if faltantes:
        raise ImproperlyConfigured(
            "Configuración S3 incompleta: faltan " + ", ".join(faltantes) + " (se necesitan las cinco SUSI_S3_*)."
        )
    opciones = {opcion: env[nombre] for nombre, opcion in _VARIABLES_S3.items()}
    opciones.update(
        addressing_style="path",
        signature_version="s3v4",
        querystring_auth=True,  # el bucket es privado: las URLs van firmadas
        default_acl=None,  # Supabase no usa ACL por objeto
        file_overwrite=False,
    )
    return {"default": {"BACKEND": "storages.backends.s3.S3Storage", "OPTIONS": opciones}, "staticfiles": ESTATICOS}


def opciones_de_base(env) -> dict:
    """OPTIONS extra de psycopg. El pooler en modo transacción (Supabase, puerto 6543) no admite prepared statements."""
    if env.get("DATABASE_DISABLE_PREPARED") == "1":
        return {"prepare_threshold": None}
    return {}


def hosts_de_render(env) -> tuple[list[str], list[str]]:
    """(ALLOWED_HOSTS, CSRF_TRUSTED_ORIGINS) que aporta Render a partir de RENDER_EXTERNAL_HOSTNAME."""
    host = env.get("RENDER_EXTERNAL_HOSTNAME", "").strip()
    if not host:
        return [], []
    return [host], [f"https://{host}"]


def encabezado_proxy_ssl(env) -> tuple[str, str] | None:
    """SECURE_PROXY_SSL_HEADER: solo se confía en X-Forwarded-Proto si se declara que hay un proxy delante."""
    if env.get("DJANGO_BEHIND_PROXY") == "1":
        return ("HTTP_X_FORWARDED_PROTO", "https")
    return None
