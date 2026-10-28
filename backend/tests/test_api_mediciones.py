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


# Final review (Review Focus 3): quien edita el borrador de otro pasa a ser quien lo cargó
def test_quien_edita_el_borrador_de_otro_no_puede_validarlo(api_para, escenario, user_factory):
    doble = user_factory(username="doble")
    Membership.objects.create(user=doble, facultad=escenario.facultad, rol=Rol.RESPONSABLE)
    Membership.objects.create(user=doble, facultad=escenario.facultad, rol=Rol.VALIDADOR)
    cliente = api_para(doble)

    editada = cliente.patch(f"{URL}{escenario.medicion.id}/", {"valor": "999"}, format="json")
    enviada = cliente.post(f"{URL}{escenario.medicion.id}/enviar/")
    validada = cliente.post(f"{URL}{escenario.medicion.id}/validar/")

    assert (editada.status_code, enviada.status_code) == (200, 200)
    assert validada.status_code == 403
    escenario.medicion.refresh_from_db()
    assert escenario.medicion.estado == EstadoMedicion.ENVIADA
    assert escenario.medicion.validado_por is None


# Final review (spec §10): los datos de ejemplo se rotulan también en la cola de validación
def test_la_medicion_expone_si_su_practica_es_ilustrativa(api_para, escenario):
    from catalog.models import Origen

    escenario.practica.origen = Origen.ILUSTRATIVA
    escenario.practica.save()

    cuerpo = api_para(escenario.responsable).get(f"{URL}{escenario.medicion.id}/").json()

    assert cuerpo["practica_origen"] == "ilustrativa"


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


# Retirar: un error descubierto después de enviar se corrige sin esperar a que el Validador la rechace
def test_el_responsable_retira_una_medicion_enviada_y_puede_corregirla(api_para, escenario):
    cliente = api_para(escenario.responsable)
    pk = escenario.medicion.id
    cliente.post(f"{URL}{pk}/enviar/")

    retirada = cliente.post(f"{URL}{pk}/retirar/")

    assert retirada.status_code == 200 and retirada.json()["estado"] == "borrador"
    assert cliente.patch(f"{URL}{pk}/", {"valor": "77"}, format="json").status_code == 200
    assert Medicion.objects.get(pk=pk).valor == Decimal("77")


def test_solo_se_retira_una_medicion_enviada(api_para, escenario):
    cliente = api_para(escenario.responsable)
    pk = escenario.medicion.id

    assert cliente.post(f"{URL}{pk}/retirar/").status_code == 400  # todavía es borrador

    cliente.post(f"{URL}{pk}/enviar/")
    api_para(escenario.validador).post(f"{URL}{pk}/validar/")
    validada = cliente.post(f"{URL}{pk}/retirar/")
    assert validada.status_code == 400
    assert Medicion.objects.get(pk=pk).estado == EstadoMedicion.VALIDADA


def test_el_validador_no_retira_mediciones(api_para, escenario):
    api_para(escenario.responsable).post(f"{URL}{escenario.medicion.id}/enviar/")

    assert api_para(escenario.validador).post(f"{URL}{escenario.medicion.id}/retirar/").status_code == 403


# Eliminar: solo un borrador, que nadie revisó todavía
def test_el_responsable_elimina_un_borrador_con_sus_evidencias(api_para, escenario):
    Evidencia.objects.create(
        medicion=escenario.medicion, tipo=TipoEvidencia.ENLACE, url="https://example.org/x", creado_por=escenario.responsable
    )
    pk = escenario.medicion.id

    respuesta = api_para(escenario.responsable).delete(f"{URL}{pk}/")

    assert respuesta.status_code == 204
    assert not Medicion.objects.filter(pk=pk).exists()
    assert not Evidencia.objects.filter(medicion_id=pk).exists()
    assert Medicion.history.filter(id=pk, history_type="-").exists()  # queda quién la eliminó


def test_no_se_elimina_una_medicion_enviada_ni_validada(api_para, escenario):
    cliente = api_para(escenario.responsable)
    pk = escenario.medicion.id
    cliente.post(f"{URL}{pk}/enviar/")
    enviada = cliente.delete(f"{URL}{pk}/")
    api_para(escenario.validador).post(f"{URL}{pk}/validar/")
    validada = cliente.delete(f"{URL}{pk}/")

    assert (enviada.status_code, validada.status_code) == (400, 400)
    assert "borrador" in str(validada.json())
    assert Medicion.objects.filter(pk=pk).exists()


def test_solo_un_responsable_de_la_facultad_elimina(api_para, escenario):
    pk = escenario.medicion.id

    assert api_para(escenario.validador).delete(f"{URL}{pk}/").status_code == 403
    assert api_para().delete(f"{URL}{pk}/").status_code in (401, 403)
    assert Medicion.objects.filter(pk=pk).exists()


def test_al_eliminar_un_borrador_se_borran_tambien_sus_archivos(
    api_para, escenario, settings, django_capture_on_commit_callbacks
):
    from django.core.files.uploadedfile import SimpleUploadedFile

    evidencia = Evidencia.objects.create(
        medicion=escenario.medicion,
        tipo=TipoEvidencia.ARCHIVO,
        archivo=SimpleUploadedFile("a.pdf", b"%PDF-1.4\n%prueba"),
        creado_por=escenario.responsable,
    )
    ruta = settings.MEDIA_ROOT / evidencia.archivo.name
    assert ruta.exists()

    with django_capture_on_commit_callbacks(execute=True):
        respuesta = api_para(escenario.responsable).delete(f"{URL}{escenario.medicion.id}/")

    assert respuesta.status_code == 204
    assert not ruta.exists()
