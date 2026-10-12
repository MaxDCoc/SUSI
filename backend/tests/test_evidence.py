import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from catalog.models import Dimension, Practica
from evidence.models import Evidencia, TipoEvidencia
from evidence.validators import TAMANO_MAXIMO, validar_archivo

pytestmark = pytest.mark.django_db

PDF = b"%PDF-1.4\n%contenido de prueba"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 16
JPG = b"\xff\xd8\xff\xe0" + b"0" * 16


@pytest.mark.parametrize(
    "nombre,contenido", [("a.pdf", PDF), ("b.PNG", PNG), ("c.jpg", JPG), ("d.jpeg", JPG)]
)
def test_acepta_pdf_png_y_jpg(nombre, contenido):
    validar_archivo(SimpleUploadedFile(nombre, contenido))


def test_acepta_un_archivo_de_exactamente_2_mb():
    contenido = PDF + b"0" * (TAMANO_MAXIMO - len(PDF))

    validar_archivo(SimpleUploadedFile("justo.pdf", contenido))


# Review Focus 2: archivos falsos o fuera de límites
@pytest.mark.parametrize(
    "nombre,contenido",
    [
        ("a.exe", PDF),
        ("a.pdf.exe", PDF),
        ("sin_extension", PDF),
        ("falso.pdf", b"MZ\x90\x00\x03\x00"),
        ("vacio.pdf", b""),
        ("imagen.png", PDF),
    ],
)
def test_rechaza_archivos_invalidos(nombre, contenido):
    with pytest.raises(ValidationError):
        validar_archivo(SimpleUploadedFile(nombre, contenido))


def test_rechaza_archivos_de_mas_de_2_mb():
    contenido = PDF + b"0" * TAMANO_MAXIMO

    with pytest.raises(ValidationError, match="2 MB"):
        validar_archivo(SimpleUploadedFile("grande.pdf", contenido))


def test_la_evidencia_debe_pertenecer_a_una_medicion_o_a_una_practica(user_factory):
    evidencia = Evidencia(tipo=TipoEvidencia.ENLACE, url="https://example.org/x", creado_por=user_factory())

    with pytest.raises(ValidationError, match="medición o a una práctica"):
        evidencia.full_clean()


def test_el_enlace_exige_url_y_el_archivo_exige_archivo(practica, user_factory):
    usuario = user_factory()

    with pytest.raises(ValidationError, match="enlace"):
        Evidencia(practica=practica, tipo=TipoEvidencia.ENLACE, creado_por=usuario).full_clean()
    with pytest.raises(ValidationError, match="archivo"):
        Evidencia(practica=practica, tipo=TipoEvidencia.ARCHIVO, creado_por=usuario).full_clean()


def test_solo_se_aceptan_enlaces_http_y_https(practica, user_factory):
    usuario = user_factory()

    Evidencia(practica=practica, tipo=TipoEvidencia.ENLACE, url="https://example.org/x", creado_por=usuario).full_clean()
    with pytest.raises(ValidationError):
        Evidencia(
            practica=practica, tipo=TipoEvidencia.ENLACE, url="javascript:alert(1)", creado_por=usuario
        ).full_clean()


def test_la_medicion_debe_pertenecer_a_la_practica_indicada(escenario_simple, facultad, user_factory):
    medicion, usuario = escenario_simple
    otra_practica = Practica.objects.create(facultad=facultad, nombre="Otra", dimension=Dimension.SOCIAL)

    evidencia = Evidencia(
        medicion=medicion,
        practica=otra_practica,
        tipo=TipoEvidencia.ENLACE,
        url="https://example.org/x",
        creado_por=usuario,
    )

    with pytest.raises(ValidationError, match="no pertenece"):
        evidencia.full_clean()


def test_el_archivo_se_guarda_con_nombre_normalizado(practica, user_factory):
    evidencia = Evidencia(
        practica=practica,
        tipo=TipoEvidencia.ARCHIVO,
        archivo=SimpleUploadedFile("Mi informe (final).pdf", PDF),
        creado_por=user_factory(),
    )
    evidencia.full_clean()
    evidencia.save()

    assert evidencia.archivo.name.startswith("evidencias/")
    assert evidencia.archivo.name.endswith(".pdf")
    assert "Mi informe" not in evidencia.archivo.name


def test_facultad_scope_id_para_evidencia_de_practica_y_de_medicion(
    practica, escenario_simple, facultad, user_factory
):
    medicion, usuario = escenario_simple
    de_practica = Evidencia(practica=practica, tipo=TipoEvidencia.ENLACE, creado_por=usuario)
    de_medicion = Evidencia(medicion=medicion, tipo=TipoEvidencia.ENLACE, creado_por=usuario)

    assert de_practica.facultad_scope_id == facultad.id
    assert de_medicion.facultad_scope_id == facultad.id
