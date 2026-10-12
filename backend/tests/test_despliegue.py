import pytest
from django.core.exceptions import ImproperlyConfigured

from susi.despliegue import encabezado_proxy_ssl, hosts_de_render, opciones_de_base, storages_desde_entorno

S3 = {
    "SUSI_S3_ENDPOINT_URL": "https://abcd.supabase.co/storage/v1/s3",
    "SUSI_S3_BUCKET": "evidencias",
    "SUSI_S3_ACCESS_KEY": "clave-de-acceso",
    "SUSI_S3_SECRET_KEY": "clave-secreta",
    "SUSI_S3_REGION": "sa-east-1",
}


# ---------- almacenamiento de archivos ----------


def test_sin_configuracion_s3_los_archivos_van_al_disco_local():
    storages = storages_desde_entorno({})

    assert storages["default"] == {"BACKEND": "django.core.files.storage.FileSystemStorage"}
    assert storages["staticfiles"]["BACKEND"] == "whitenoise.storage.CompressedStaticFilesStorage"


def test_con_configuracion_s3_los_archivos_van_a_un_bucket_privado():
    storages = storages_desde_entorno(S3)

    assert storages["default"]["BACKEND"] == "storages.backends.s3.S3Storage"
    opciones = storages["default"]["OPTIONS"]
    assert opciones["endpoint_url"] == S3["SUSI_S3_ENDPOINT_URL"]
    assert opciones["bucket_name"] == "evidencias"
    assert opciones["region_name"] == "sa-east-1"
    assert opciones["access_key"] == "clave-de-acceso"
    assert opciones["secret_key"] == "clave-secreta"
    assert opciones["addressing_style"] == "path"
    assert opciones["querystring_auth"] is True  # bucket privado: las URLs van firmadas
    assert opciones["default_acl"] is None  # Supabase no usa ACL por objeto
    assert opciones["file_overwrite"] is False
    assert storages["staticfiles"]["BACKEND"] == "whitenoise.storage.CompressedStaticFilesStorage"


def test_una_configuracion_s3_incompleta_falla_nombrando_lo_que_falta():
    incompleta = {k: v for k, v in S3.items() if k not in ("SUSI_S3_BUCKET", "SUSI_S3_SECRET_KEY")}

    with pytest.raises(ImproperlyConfigured) as error:
        storages_desde_entorno(incompleta)

    assert "SUSI_S3_BUCKET" in str(error.value)
    assert "SUSI_S3_SECRET_KEY" in str(error.value)
    assert "clave-de-acceso" not in str(error.value)  # nunca se imprimen los valores


# ---------- base de datos detrás de un pooler ----------


def test_por_defecto_la_base_no_cambia_las_opciones_de_conexion():
    assert opciones_de_base({}) == {}


def test_se_pueden_desactivar_los_prepared_statements_para_el_pooler_en_modo_transaccion():
    assert opciones_de_base({"DATABASE_DISABLE_PREPARED": "1"}) == {"prepare_threshold": None}
    assert opciones_de_base({"DATABASE_DISABLE_PREPARED": "0"}) == {}


# ---------- Render y proxy HTTPS ----------


def test_render_aporta_su_host_y_su_origen_https():
    hosts, origenes = hosts_de_render({"RENDER_EXTERNAL_HOSTNAME": "susi.onrender.com"})

    assert hosts == ["susi.onrender.com"]
    assert origenes == ["https://susi.onrender.com"]


def test_fuera_de_render_no_se_agrega_nada():
    assert hosts_de_render({}) == ([], [])


def test_el_encabezado_de_proxy_solo_se_confia_si_se_declara():
    assert encabezado_proxy_ssl({"DJANGO_BEHIND_PROXY": "1"}) == ("HTTP_X_FORWARDED_PROTO", "https")
    assert encabezado_proxy_ssl({}) is None
    assert encabezado_proxy_ssl({"DJANGO_BEHIND_PROXY": "0"}) is None
