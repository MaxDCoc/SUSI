import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

pytestmark = pytest.mark.django_db

URL = "/api/evidencias/"
PDF = b"%PDF-1.4\n%prueba"


def subir(cliente, escenario, nombre="factura.pdf", contenido=PDF):
    return cliente.post(
        URL,
        {
            "medicion": escenario.medicion.id,
            "tipo": "archivo",
            "archivo": SimpleUploadedFile(nombre, contenido),
            "descripcion": "Factura",
        },
        format="multipart",
    )


def test_responsable_sube_un_pdf(api_para, escenario):
    respuesta = subir(api_para(escenario.responsable), escenario)

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert "archivo" not in cuerpo  # nunca se expone la ruta interna
    assert cuerpo["archivo_descarga"].endswith("/descargar/")
    assert cuerpo["creado_por_nombre"] == "responsable"


# Review Focus 2: archivos falsos o fuera de límites
@pytest.mark.parametrize(
    "nombre,contenido",
    [("a.exe", PDF), ("a.pdf.exe", PDF), ("falso.pdf", b"MZ\x90\x00"), ("vacio.pdf", b"")],
)
def test_archivos_invalidos_dan_400(api_para, escenario, nombre, contenido):
    respuesta = subir(api_para(escenario.responsable), escenario, nombre, contenido)

    assert respuesta.status_code == 400


# Final review: la evidencia que llega después de validar nadie la vio
def test_no_se_agrega_evidencia_a_una_medicion_ya_validada(api_para, escenario):
    from indicators.models import EstadoMedicion

    escenario.medicion.estado = EstadoMedicion.VALIDADA
    escenario.medicion.save()

    respuesta = api_para(escenario.responsable).post(
        URL,
        {"medicion": escenario.medicion.id, "tipo": "enlace", "url": "https://example.org/tarde"},
        format="json",
    )

    assert respuesta.status_code == 400
    assert escenario.medicion.evidencias.count() == 0


def test_enlace_https_valido_y_javascript_invalido(api_para, escenario):
    cliente = api_para(escenario.responsable)
    base = {"medicion": escenario.medicion.id, "tipo": "enlace"}

    ok = cliente.post(URL, {**base, "url": "https://example.org/factura"}, format="json")
    assert ok.status_code == 201

    mal = cliente.post(URL, {**base, "url": "javascript:alert(1)"}, format="json")
    assert mal.status_code == 400


def test_la_evidencia_necesita_medicion_o_practica(api_para, escenario):
    respuesta = api_para(escenario.responsable).post(
        URL, {"tipo": "enlace", "url": "https://example.org/x"}, format="json"
    )

    assert respuesta.status_code == 400


def test_un_validador_no_sube_evidencias(api_para, escenario):
    assert subir(api_para(escenario.validador), escenario).status_code == 403


def test_descargar_requiere_sesion_y_entrega_el_archivo_adjunto(api_para, escenario):
    creada = subir(api_para(escenario.responsable), escenario).json()

    anonimo = api_para().get(creada["archivo_descarga"])
    assert anonimo.status_code == 403

    respuesta = api_para(escenario.validador).get(creada["archivo_descarga"])
    assert respuesta.status_code == 200
    assert b"".join(respuesta.streaming_content) == PDF
    assert "attachment" in respuesta["Content-Disposition"]


def test_descargar_un_enlace_da_404(api_para, escenario):
    creada = api_para(escenario.responsable).post(
        URL,
        {"medicion": escenario.medicion.id, "tipo": "enlace", "url": "https://example.org/x"},
        format="json",
    ).json()

    respuesta = api_para(escenario.validador).get(f"{URL}{creada['id']}/descargar/")

    assert respuesta.status_code == 404
