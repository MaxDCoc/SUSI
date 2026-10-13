import pytest

pytestmark = pytest.mark.django_db

URL = "/api/indicadores/"


def payload(practica, **extra):
    return {
        "practica": practica.id,
        "nombre": "Energía solar generada",
        "formula": "Suma mensual de kWh",
        "unidad": "kWh",
        "periodicidad": "mensual",
        "tipo": "institucional",
        **extra,
    }


def test_responsable_crea_un_indicador(api_para, escenario):
    respuesta = api_para(escenario.responsable).post(URL, payload(escenario.practica, meta="5000"), format="json")

    assert respuesta.status_code == 201
    assert respuesta.json()["meta"] == "5000.0000"


def test_un_validador_no_crea_indicadores(api_para, escenario):
    assert api_para(escenario.validador).post(URL, payload(escenario.practica), format="json").status_code == 403


def test_lista_filtra_por_practica_y_valida_el_filtro(api_para, escenario):
    cliente = api_para(escenario.responsable)

    assert cliente.get(URL, {"practica": escenario.practica.id}).json()["count"] == 1
    assert cliente.get(URL, {"practica": "abc"}).status_code == 400


def test_no_se_puede_cambiar_la_practica_de_un_indicador(api_para, escenario, facultad):
    from catalog.models import Dimension, Practica

    otra = Practica.objects.create(facultad=facultad, nombre="Otra", dimension=Dimension.SOCIAL)

    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.indicador.id}/", {"practica": otra.id}, format="json"
    )

    assert respuesta.status_code == 400


def test_responsable_edita_la_meta(api_para, escenario):
    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.indicador.id}/", {"meta": "100"}, format="json"
    )

    assert respuesta.status_code == 200


def test_responsable_quita_la_meta(api_para, escenario):
    cliente = api_para(escenario.responsable)
    url = f"{URL}{escenario.indicador.id}/"
    assert cliente.patch(url, {"meta": "100"}, format="json").json()["meta"] == "100.0000"

    respuesta = cliente.patch(url, {"meta": None}, format="json")

    assert respuesta.status_code == 200
    assert respuesta.json()["meta"] is None


def test_un_validador_no_edita_la_meta(api_para, escenario):
    respuesta = api_para(escenario.validador).patch(
        f"{URL}{escenario.indicador.id}/", {"meta": "100"}, format="json"
    )

    assert respuesta.status_code == 403
