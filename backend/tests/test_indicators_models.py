from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from indicators.models import EstadoMedicion, Indicador, Medicion, Periodicidad, TipoIndicador

pytestmark = pytest.mark.django_db


def test_indicador_solo_exige_los_campos_minimos(practica):
    indicador = Indicador(
        practica=practica,
        nombre="Energía",
        formula="suma de kWh",
        unidad="kWh",
        periodicidad=Periodicidad.MENSUAL,
        tipo=TipoIndicador.INSTITUCIONAL,
    )

    indicador.full_clean()  # sin fuente, línea base, meta ni tolerancia


def test_medicion_nueva_es_borrador(indicador, user_factory):
    medicion = Medicion.objects.create(
        indicador=indicador, periodo="2026-01", valor=Decimal("12.5"), cargado_por=user_factory()
    )

    assert medicion.estado == EstadoMedicion.BORRADOR
    assert medicion.validado_por is None


@pytest.mark.parametrize("periodo", ["2026-01", "2026-12"])
def test_periodo_valido(indicador, user_factory, periodo):
    medicion = Medicion(
        indicador=indicador, periodo=periodo, valor=Decimal("1"), cargado_por=user_factory()
    )

    medicion.full_clean()


# Review Focus 1: períodos mal formados
@pytest.mark.parametrize(
    "periodo", ["2026-13", "2026-00", "2026-1", "26-01", "", "2026/01", "2026-01\n", "enero 2026"]
)
def test_periodo_invalido_se_rechaza(indicador, user_factory, periodo):
    medicion = Medicion(
        indicador=indicador, periodo=periodo, valor=Decimal("1"), cargado_por=user_factory()
    )

    with pytest.raises(ValidationError):
        medicion.full_clean()


def test_facultad_scope_id_viene_de_la_practica(indicador, facultad, user_factory):
    medicion = Medicion(
        indicador=indicador, periodo="2026-01", valor=Decimal("1"), cargado_por=user_factory()
    )

    assert indicador.facultad_scope_id == facultad.id
    assert medicion.facultad_scope_id == facultad.id


def test_cada_cambio_de_medicion_queda_en_el_historial(indicador, user_factory):
    medicion = Medicion.objects.create(
        indicador=indicador, periodo="2026-01", valor=Decimal("1"), cargado_por=user_factory()
    )

    medicion.valor = Decimal("2")
    medicion.save()

    assert medicion.history.count() == 2
