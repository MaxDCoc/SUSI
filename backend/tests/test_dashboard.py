from decimal import Decimal

import pytest

from catalog.models import ODS, Dimension, Estado, Facultad, Practica, Region
from indicators.models import Indicador, Periodicidad, TipoIndicador
from tests.helpers import nueva_medicion_validada

pytestmark = pytest.mark.django_db

EMBUDO = "/api/dashboard/embudo/"
RESUMEN = "/api/dashboard/resumen/"


def crear(facultad, nombre, estado=Estado.IDENTIFICADA, dimension=Dimension.AMBIENTAL, responsable=None, ods=()):
    practica = Practica.objects.create(
        facultad=facultad, nombre=nombre, dimension=dimension, estado=estado, responsable=responsable
    )
    if ods:
        practica.ods.set(ODS.objects.filter(numero__in=ods))
    return practica


@pytest.fixture
def ods(db):
    ODS.objects.create(numero=7, nombre="Energía asequible y no contaminante")
    ODS.objects.create(numero=13, nombre="Acción por el clima")


def test_el_tablero_requiere_sesion(api_para):
    assert api_para().get(RESUMEN).status_code == 403
    assert api_para().get(EMBUDO).status_code == 403


def test_embudo_cuenta_las_practicas_por_estado(api_para, user_factory, facultad):
    crear(facultad, "A")
    crear(facultad, "B")
    crear(facultad, "C", Estado.FORMALIZADA)
    crear(facultad, "D", Estado.MEDIDA)

    cuerpo = api_para(user_factory()).get(EMBUDO).json()

    assert cuerpo == {
        "total": 4,
        "estados": {"identificada": 2, "formalizada": 1, "medida": 1, "optimizada": 0},
    }


# Review Focus 4: sin datos todavía
def test_resumen_sin_practicas_devuelve_ceros_y_no_falla(api_para, user_factory, facultad):
    cuerpo = api_para(user_factory()).get(RESUMEN).json()

    assert cuerpo["total_practicas"] == 0
    assert cuerpo["kpis"]["con_responsable"] == {"cantidad": 0, "porcentaje": 0.0}
    assert cuerpo["cobertura"] == {"facultades_con_practicas": 0, "facultades_total": 1, "porcentaje": 0.0}
    assert cuerpo["embudo"] == {"identificada": 0, "formalizada": 0, "medida": 0, "optimizada": 0}
    assert cuerpo["por_facultad"] == [] and cuerpo["por_ods"] == []


def test_kpis_de_resumen(api_para, escenario):
    # p1 (la del escenario): responsable + indicador + medición validada con evidencia
    escenario.practica.responsable = escenario.responsable
    escenario.practica.save()
    nueva_medicion_validada(escenario.indicador, escenario.responsable, escenario.validador, "2026-02")
    # p2: solo responsable; p3: nada
    crear(escenario.facultad, "p2", responsable=escenario.responsable)
    crear(escenario.facultad, "p3")

    cuerpo = api_para(escenario.responsable).get(RESUMEN).json()

    assert cuerpo["total_practicas"] == 3
    assert cuerpo["kpis"]["con_responsable"] == {"cantidad": 2, "porcentaje": 66.7}
    assert cuerpo["kpis"]["con_indicador"] == {"cantidad": 1, "porcentaje": 33.3}
    assert cuerpo["kpis"]["con_evidencia_validada"] == {"cantidad": 1, "porcentaje": 33.3}


# Final review (spec §10): el tablero avisa cuántas prácticas son datos de ejemplo
def test_el_resumen_cuenta_las_practicas_ilustrativas(api_para, escenario):
    from catalog.models import Origen

    Practica.objects.create(
        facultad=escenario.facultad, nombre="Ejemplo", dimension=Dimension.SOCIAL, origen=Origen.ILUSTRATIVA
    )

    cuerpo = api_para(escenario.responsable).get(RESUMEN).json()

    assert cuerpo["total_practicas"] == 2
    assert cuerpo["ilustrativas"] == 1


def test_una_medicion_validada_sin_evidencia_no_cuenta_como_evidencia_validada(api_para, escenario):
    nueva_medicion_validada(
        escenario.indicador, escenario.responsable, escenario.validador, "2026-02", con_evidencia=False
    )

    cuerpo = api_para(escenario.responsable).get(RESUMEN).json()

    assert cuerpo["kpis"]["con_evidencia_validada"]["cantidad"] == 0


def test_agrupaciones_por_facultad_region_dimension_y_ods(api_para, user_factory, facultad, otra_facultad, ods):
    crear(facultad, "a", Estado.MEDIDA, Dimension.AMBIENTAL, ods=[7, 13])
    crear(facultad, "b", Estado.IDENTIFICADA, Dimension.SOCIAL, ods=[13])
    crear(otra_facultad, "c", Estado.FORMALIZADA, Dimension.AMBIENTAL)

    cuerpo = api_para(user_factory()).get(RESUMEN).json()

    assert [g["etiqueta"] for g in cuerpo["por_facultad"]] == ["Resistencia", "Rafaela"]
    assert cuerpo["por_facultad"][0]["total"] == 2 and cuerpo["por_facultad"][0]["medida"] == 1
    assert [g["etiqueta"] for g in cuerpo["por_region"]] == ["NEA", "Centro"]
    dimensiones = {g["etiqueta"]: g["total"] for g in cuerpo["por_dimension"]}
    assert dimensiones == {"Ambiental": 2, "Social": 1}
    por_ods = {g["clave"]: g["total"] for g in cuerpo["por_ods"]}
    assert por_ods == {7: 1, 13: 2}
    assert cuerpo["por_ods"][0]["etiqueta"].startswith("ODS 13")  # el de más prácticas primero


def test_filtros_por_region_dimension_y_ods(api_para, user_factory, facultad, otra_facultad, ods):
    crear(facultad, "a", dimension=Dimension.AMBIENTAL, ods=[7])
    crear(otra_facultad, "b", dimension=Dimension.SOCIAL, ods=[13])
    cliente = api_para(user_factory())

    assert cliente.get(RESUMEN, {"region": otra_facultad.region_id}).json()["total_practicas"] == 1
    assert cliente.get(RESUMEN, {"facultad": facultad.id}).json()["total_practicas"] == 1
    assert cliente.get(RESUMEN, {"dimension": "social"}).json()["total_practicas"] == 1
    assert cliente.get(RESUMEN, {"ods": 7}).json()["total_practicas"] == 1


@pytest.mark.parametrize("filtro", ["facultad=abc", "ods=99", "ods=0", "dimension=otra", "region=-1"])
def test_filtros_invalidos_dan_400(api_para, user_factory, filtro):
    assert api_para(user_factory()).get(f"{RESUMEN}?{filtro}").status_code == 400
    assert api_para(user_factory()).get(f"{EMBUDO}?{filtro}").status_code == 400


def test_la_cobertura_cuenta_solo_facultades_regionales(api_para, user_factory, facultad):
    central = Facultad.objects.create(
        nombre="Rectorado", region=Region.objects.create(nombre="Nivel Central"), es_nivel_central=True
    )
    crear(facultad, "en la facultad")
    crear(central, "en el rectorado")

    cobertura = api_para(user_factory()).get(RESUMEN).json()["cobertura"]

    assert cobertura == {"facultades_con_practicas": 1, "facultades_total": 1, "porcentaje": 100.0}


def test_el_resumen_se_actualiza_apenas_cambian_los_datos(api_para, user_factory, facultad):
    cliente = api_para(user_factory())
    assert cliente.get(RESUMEN).json()["total_practicas"] == 0

    crear(facultad, "nueva")

    assert cliente.get(RESUMEN).json()["total_practicas"] == 1


def test_el_resumen_no_hace_una_consulta_por_fila(api_para, user_factory, facultad, ods, django_assert_max_num_queries):
    for i in range(15):
        practica = crear(facultad, f"p{i}", ods=[7])
        Indicador.objects.create(
            practica=practica,
            nombre="i",
            formula="f",
            unidad="u",
            periodicidad=Periodicidad.MENSUAL,
            tipo=TipoIndicador.INSTITUCIONAL,
            meta=Decimal("1"),
        )
    cliente = api_para(user_factory())

    with django_assert_max_num_queries(14):
        assert cliente.get(RESUMEN).status_code == 200
