from decimal import Decimal

import pytest

from accounts.models import Membership, Rol
from evidence.models import Evidencia, TipoEvidencia
from indicators.models import EstadoMedicion, Medicion

pytestmark = pytest.mark.django_db

URL = "/api/mediciones/"


def nueva(escenario, **extra):
    return {"indicador": escenario.indicador.id, "periodo": "2026-02", "valor": "12.5", **extra}


def test_responsable_carga_una_medicion_en_borrador(api_para, escenario):
    respuesta = api_para(escenario.responsable).post(URL, nueva(escenario), format="json")

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "borrador"
    assert cuerpo["cargado_por_nombre"] == "responsable"
    assert cuerpo["evidencias"] == []


def test_el_estado_y_la_validacion_no_se_fijan_por_payload(api_para, escenario):
    respuesta = api_para(escenario.responsable).post(
        URL, nueva(escenario, estado="validada", validado_por=escenario.validador.id), format="json"
    )

    assert respuesta.status_code == 201
    assert respuesta.json()["estado"] == "borrador"
    assert respuesta.json()["validado_por"] is None


# Review Focus 1: período y valor mal formados nunca deben dar 500
@pytest.mark.parametrize(
    "campo,valor",
    [
        ("periodo", "2026-13"),
        ("periodo", "2026-1"),
        ("periodo", ""),
        ("valor", "NaN"),
        ("valor", "Infinity"),
        ("valor", "1e999"),
        ("valor", "abc"),
        ("valor", ""),
    ],
)
def test_periodo_y_valor_invalidos_dan_400(api_para, escenario, campo, valor):
    respuesta = api_para(escenario.responsable).post(URL, nueva(escenario, **{campo: valor}), format="json")

    assert respuesta.status_code == 400
    assert campo in respuesta.json()


def test_un_validador_no_carga_mediciones(api_para, escenario):
    assert api_para(escenario.validador).post(URL, nueva(escenario), format="json").status_code == 403


def test_flujo_enviar_y_validar(api_para, escenario):
    pk = escenario.medicion.id

    enviada = api_para(escenario.responsable).post(f"{URL}{pk}/enviar/")
    assert enviada.status_code == 200 and enviada.json()["estado"] == "enviada"

    validada = api_para(escenario.validador).post(f"{URL}{pk}/validar/", {"comentario": "Conforme"}, format="json")
    assert validada.status_code == 200
    cuerpo = validada.json()
    assert cuerpo["estado"] == "validada"
    assert cuerpo["validado_por_nombre"] == "validador"
    assert cuerpo["comentario_validacion"] == "Conforme"


def test_un_responsable_sin_rol_de_validador_recibe_403(api_para, escenario):
    api_para(escenario.responsable).post(f"{URL}{escenario.medicion.id}/enviar/")

    respuesta = api_para(escenario.responsable).post(f"{URL}{escenario.medicion.id}/validar/")

    assert respuesta.status_code == 403


def test_el_validador_no_valida_lo_propio(api_para, escenario):
    Membership.objects.create(user=escenario.responsable, facultad=escenario.facultad, rol=Rol.VALIDADOR)
    api_para(escenario.responsable).post(f"{URL}{escenario.medicion.id}/enviar/")

    respuesta = api_para(escenario.responsable).post(f"{URL}{escenario.medicion.id}/validar/")

    assert respuesta.status_code == 403
    assert "no puede validarla" in respuesta.json()["detail"]


def test_la_doble_validacion_da_400_y_no_pisa_al_primero(api_para, escenario, user_factory):
    segundo = user_factory(username="segundo")
    Membership.objects.create(user=segundo, facultad=escenario.facultad, rol=Rol.VALIDADOR)
    pk = escenario.medicion.id
    api_para(escenario.responsable).post(f"{URL}{pk}/enviar/")
    assert api_para(escenario.validador).post(f"{URL}{pk}/validar/").status_code == 200

    repetida = api_para(segundo).post(f"{URL}{pk}/validar/")

    assert repetida.status_code == 400
    assert Medicion.objects.get(pk=pk).validado_por == escenario.validador


def test_no_se_edita_una_medicion_enviada_pero_si_en_borrador(api_para, escenario):
    cliente = api_para(escenario.responsable)
    pk = escenario.medicion.id

    assert cliente.patch(f"{URL}{pk}/", {"valor": "99"}, format="json").status_code == 200

    cliente.post(f"{URL}{pk}/enviar/")
    bloqueada = cliente.patch(f"{URL}{pk}/", {"valor": "1"}, format="json")
    assert bloqueada.status_code == 400
    assert "borrador" in str(bloqueada.json())
    assert Medicion.objects.get(pk=pk).valor == Decimal("99")


def test_rechazar_exige_comentario_y_se_puede_reabrir(api_para, escenario):
    pk = escenario.medicion.id
    api_para(escenario.responsable).post(f"{URL}{pk}/enviar/")

    sin_comentario = api_para(escenario.validador).post(f"{URL}{pk}/rechazar/", {}, format="json")
    assert sin_comentario.status_code == 400

    rechazada = api_para(escenario.validador).post(f"{URL}{pk}/rechazar/", {"comentario": "Falta la fuente"}, format="json")
    assert rechazada.status_code == 200 and rechazada.json()["estado"] == "rechazada"

    reabierta = api_para(escenario.responsable).post(f"{URL}{pk}/reabrir/")
    assert reabierta.status_code == 200 and reabierta.json()["estado"] == "borrador"


def test_la_lista_filtra_trae_evidencias_anidadas_y_valida_filtros(api_para, escenario):
    Evidencia.objects.create(
        medicion=escenario.medicion,
        tipo=TipoEvidencia.ENLACE,
        url="https://example.org/factura",
        descripcion="Factura",
        creado_por=escenario.responsable,
    )
    cliente = api_para(escenario.validador)

    cuerpo = cliente.get(URL, {"estado": "borrador"}).json()
    assert cuerpo["count"] == 1
    medicion = cuerpo["results"][0]
    assert medicion["n_evidencias"] == 1
    assert medicion["evidencias"][0]["url"] == "https://example.org/factura"
    assert medicion["practica_id"] == escenario.practica.id
    assert medicion["facultad_id"] == escenario.facultad.id

    assert cliente.get(URL, {"estado": "validada"}).json()["count"] == 0
    assert cliente.get(URL, {"indicador": "abc"}).status_code == 400


def test_la_lista_no_tiene_consultas_n_mas_uno(api_para, escenario, django_assert_max_num_queries):
    for i in range(10):
        medicion = Medicion.objects.create(
            indicador=escenario.indicador,
            periodo=f"2025-{i + 1:02d}",
            valor=Decimal("1"),
            cargado_por=escenario.responsable,
            estado=EstadoMedicion.ENVIADA,
        )
        Evidencia.objects.create(
            medicion=medicion, tipo=TipoEvidencia.ENLACE, url="https://example.org/x", creado_por=escenario.responsable
        )
    cliente = api_para(escenario.validador)

    with django_assert_max_num_queries(8):
        respuesta = cliente.get(URL)

    assert respuesta.status_code == 200
