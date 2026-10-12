"""Las evidencias contra un servidor S3 real (emulado con moto): lo que usará Supabase Storage en producción."""

import socket

import boto3
import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from moto.server import ThreadedMotoServer

from evidence.models import Evidencia
from susi.despliegue import storages_desde_entorno

pytestmark = pytest.mark.django_db

URL = "/api/evidencias/"
PDF = b"%PDF-1.4\n%prueba en el bucket"
BUCKET = "evidencias"


@pytest.fixture(scope="module")
def servidor_s3():
    with socket.socket() as libre:
        libre.bind(("127.0.0.1", 0))
        puerto = libre.getsockname()[1]
    servidor = ThreadedMotoServer(ip_address="127.0.0.1", port=puerto, verbose=False)
    servidor.start()
    endpoint = f"http://127.0.0.1:{puerto}"
    boto3.client(
        "s3", endpoint_url=endpoint, aws_access_key_id="k", aws_secret_access_key="s", region_name="us-east-1"
    ).create_bucket(Bucket=BUCKET)
    yield endpoint
    servidor.stop()


@pytest.fixture
def s3(servidor_s3, settings):
    settings.STORAGES = storages_desde_entorno(
        {
            "SUSI_S3_ENDPOINT_URL": servidor_s3,
            "SUSI_S3_BUCKET": BUCKET,
            "SUSI_S3_ACCESS_KEY": "k",
            "SUSI_S3_SECRET_KEY": "s",
            "SUSI_S3_REGION": "us-east-1",
        }
    )
    return boto3.client(
        "s3", endpoint_url=servidor_s3, aws_access_key_id="k", aws_secret_access_key="s", region_name="us-east-1"
    )


def subir(cliente, escenario):
    return cliente.post(
        URL,
        {
            "medicion": escenario.medicion.id,
            "tipo": "archivo",
            "archivo": SimpleUploadedFile("factura.pdf", PDF),
            "descripcion": "Factura",
        },
        format="multipart",
    )


def test_el_pdf_queda_en_el_bucket_y_no_en_el_disco_local(api_para, escenario, s3, settings):
    respuesta = subir(api_para(escenario.responsable), escenario)

    assert respuesta.status_code == 201
    clave = Evidencia.objects.get().archivo.name
    assert clave.startswith("evidencias/") and clave.endswith(".pdf")
    assert s3.get_object(Bucket=BUCKET, Key=clave)["Body"].read() == PDF
    assert not (settings.MEDIA_ROOT / clave).exists()


def test_la_api_descarga_el_pdf_desde_el_bucket_solo_con_sesion(api_para, escenario, s3):
    creada = subir(api_para(escenario.responsable), escenario).json()

    assert api_para().get(creada["archivo_descarga"]).status_code == 403
    respuesta = api_para(escenario.validador).get(creada["archivo_descarga"])
    assert respuesta.status_code == 200
    assert b"".join(respuesta.streaming_content) == PDF
    assert "attachment" in respuesta["Content-Disposition"]
