import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import ProtectedError

from catalog.models import ODS, Dimension, Estado, Facultad, Origen, Practica

pytestmark = pytest.mark.django_db


def test_practica_nueva_es_identificada_y_no_exige_responsable(facultad):
    practica = Practica.objects.create(
        facultad=facultad, nombre="Separación de residuos", dimension=Dimension.AMBIENTAL
    )

    assert practica.estado == Estado.IDENTIFICADA
    assert practica.responsable is None
    assert practica.origen == Origen.CARGADA


def test_estado_siguiente_y_anterior(facultad):
    practica = Practica(facultad=facultad, nombre="x", dimension=Dimension.SOCIAL)

    assert practica.estado_anterior() is None
    assert practica.estado_siguiente() == Estado.FORMALIZADA

    practica.estado = Estado.OPTIMIZADA
    assert practica.estado_siguiente() is None
    assert practica.estado_anterior() == Estado.MEDIDA


def test_facultad_scope_id_es_la_facultad_de_la_practica(facultad):
    practica = Practica(facultad=facultad, nombre="x", dimension=Dimension.SOCIAL)

    assert practica.facultad_scope_id == facultad.id


def test_nombre_de_facultad_es_unico(facultad, region):
    with pytest.raises(IntegrityError), transaction.atomic():
        Facultad.objects.create(nombre=facultad.nombre, region=region)


def test_no_se_puede_borrar_una_region_con_facultades(region, facultad):
    with pytest.raises(ProtectedError):
        region.delete()


def test_ods_valida_rango_1_a_17():
    with pytest.raises(ValidationError):
        ODS(numero=18, nombre="Inexistente").full_clean()


def test_cada_cambio_de_practica_queda_en_el_historial(facultad):
    practica = Practica.objects.create(facultad=facultad, nombre="Original", dimension=Dimension.SOCIAL)

    practica.nombre = "Modificada"
    practica.save()

    assert practica.history.count() == 2
    assert practica.history.first().nombre == "Modificada"
