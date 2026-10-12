import pytest

from accounts.models import Membership, Rol
from catalog.models import ODS, Dimension, Estado, Practica
from tests.helpers import nueva_medicion_validada

pytestmark = pytest.mark.django_db

URL = "/api/practicas/"


def payload(facultad, **extra):
    return {"facultad": facultad.id, "nombre": "Separación de residuos", "dimension": "ambiental", **extra}


def test_anonimo_no_puede_listar(api_para):
    assert api_para().get(URL).status_code == 403


def test_lista_paginada_de_20(api_para, escenario):
    Practica.objects.bulk_create(
        [Practica(facultad=escenario.facultad, nombre=f"P{i}", dimension=Dimension.SOCIAL) for i in range(24)]
    )

    respuesta = api_para(escenario.responsable).get(URL)

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["count"] == 25  # 24 + la práctica del escenario
    assert len(cuerpo["results"]) == 20
    assert cuerpo["next"] is not None


def test_lista_filtra_por_estado_y_rechaza_filtros_invalidos(api_para, escenario):
    Practica.objects.create(
        facultad=escenario.facultad, nombre="Otra", dimension=Dimension.SOCIAL, estado=Estado.MEDIDA
    )
    cliente = api_para(escenario.responsable)

    filtrada = cliente.get(URL, {"estado": "medida"}).json()
    assert filtrada["count"] == 1 and filtrada["results"][0]["nombre"] == "Otra"

    assert cliente.get(URL, {"facultad": "abc"}).status_code == 400


def test_responsable_crea_practica_en_su_facultad(api_para, escenario):
    ods = ODS.objects.create(numero=12, nombre="Producción y consumo responsables")

    respuesta = api_para(escenario.responsable).post(
        URL,
        payload(escenario.facultad, estado="optimizada", origen="ilustrativa", ods=[ods.numero]),
        format="json",
    )

    assert respuesta.status_code == 201
    cuerpo = respuesta.json()
    assert cuerpo["estado"] == "identificada"  # el estado no se puede fijar desde la API
    assert cuerpo["origen"] == "cargada"
    assert cuerpo["ods"] == [12]
    assert cuerpo["facultad_nombre"] == "Resistencia"


def test_responsable_no_crea_en_otra_facultad(api_para, escenario, otra_facultad):
    respuesta = api_para(escenario.responsable).post(URL, payload(otra_facultad), format="json")

    assert respuesta.status_code == 403


def test_un_validador_no_crea_practicas(api_para, escenario):
    respuesta = api_para(escenario.validador).post(URL, payload(escenario.facultad), format="json")

    assert respuesta.status_code == 403


def test_no_se_puede_borrar_una_practica(api_para, escenario):
    respuesta = api_para(escenario.responsable).delete(f"{URL}{escenario.practica.id}/")

    assert respuesta.status_code == 405


def test_editar_practica_de_otra_facultad_es_403(api_para, escenario, otra_facultad, user_factory):
    ajeno = user_factory()
    Membership.objects.create(user=ajeno, facultad=otra_facultad, rol=Rol.RESPONSABLE)

    respuesta = api_para(ajeno).patch(f"{URL}{escenario.practica.id}/", {"nombre": "x"}, format="json")

    assert respuesta.status_code == 403


def test_responsable_edita_su_practica(api_para, escenario):
    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.practica.id}/", {"nombre": "Paneles solares 2"}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["nombre"] == "Paneles solares 2"


def test_no_se_puede_mover_una_practica_a_una_facultad_ajena(api_para, escenario, otra_facultad):
    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.practica.id}/", {"facultad": otra_facultad.id}, format="json"
    )

    assert respuesta.status_code == 403


def test_el_responsable_puede_asumir_la_responsabilidad_de_una_practica(api_para, escenario):
    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.practica.id}/", {"responsable": escenario.responsable.id}, format="json"
    )

    assert respuesta.status_code == 200
    assert respuesta.json()["responsable_nombre"] == "responsable"


def test_promover_sin_responsable_devuelve_400_con_el_motivo(api_para, escenario):
    respuesta = api_para(escenario.responsable).post(f"{URL}{escenario.practica.id}/promover/")

    assert respuesta.status_code == 400
    assert "responsable" in str(respuesta.json()).lower()


def test_promover_con_responsable_pasa_a_formalizada(api_para, escenario):
    escenario.practica.responsable = escenario.responsable
    escenario.practica.save()

    respuesta = api_para(escenario.responsable).post(f"{URL}{escenario.practica.id}/promover/")

    assert respuesta.status_code == 200
    assert respuesta.json()["estado"] == "formalizada"


def test_promover_una_practica_inexistente_da_404(api_para, escenario):
    assert api_para(escenario.responsable).post(f"{URL}99999/promover/").status_code == 404


def test_solo_el_administrador_retrocede(api_para, escenario, user_factory):
    escenario.practica.estado = Estado.FORMALIZADA
    escenario.practica.save()

    como_responsable = api_para(escenario.responsable).post(
        f"{URL}{escenario.practica.id}/retroceder/", {"motivo": "Error"}, format="json"
    )
    assert como_responsable.status_code == 403

    como_admin = api_para(user_factory(is_superuser=True)).post(
        f"{URL}{escenario.practica.id}/retroceder/", {"motivo": "Error de carga"}, format="json"
    )
    assert como_admin.status_code == 200
    assert como_admin.json()["estado"] == "identificada"


# Final review: doble clic en "Promover" y práctica movida entre facultades
def test_promover_con_el_estado_que_ve_el_cliente_evita_saltar_dos_niveles(api_para, escenario):
    escenario.practica.responsable = escenario.responsable
    escenario.practica.save()
    # Con una medición validada con evidencia, el segundo clic llegaría hasta "medida" si no se lo frena.
    nueva_medicion_validada(escenario.indicador, escenario.responsable, escenario.validador, "2026-02")
    cliente = api_para(escenario.responsable)
    url = f"{URL}{escenario.practica.id}/promover/"

    primero = cliente.post(url, {"desde": "identificada"}, format="json")
    segundo = cliente.post(url, {"desde": "identificada"}, format="json")  # el doble clic

    assert primero.status_code == 200
    assert segundo.status_code == 400
    escenario.practica.refresh_from_db()
    assert escenario.practica.estado == Estado.FORMALIZADA


def test_no_se_mueve_una_practica_a_otra_facultad_ni_siendo_responsable_de_ambas(
    api_para, escenario, otra_facultad
):
    Membership.objects.create(user=escenario.responsable, facultad=otra_facultad, rol=Rol.RESPONSABLE)

    respuesta = api_para(escenario.responsable).patch(
        f"{URL}{escenario.practica.id}/", {"facultad": otra_facultad.id}, format="json"
    )

    assert respuesta.status_code == 400
    escenario.practica.refresh_from_db()
    assert escenario.practica.facultad == escenario.facultad


def test_catalogos_expone_regiones_facultades_ods_y_enumeraciones(api_para, escenario):
    ODS.objects.create(numero=7, nombre="Energía asequible y no contaminante")

    respuesta = api_para(escenario.responsable).get("/api/catalogos/")

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert [f["nombre"] for f in cuerpo["facultades"]] == ["Resistencia"]
    assert cuerpo["ods"] == [{"numero": 7, "nombre": "Energía asequible y no contaminante"}]
    assert [d["valor"] for d in cuerpo["dimensiones"]] == ["ambiental", "social", "economica", "institucional"]
    assert [e["valor"] for e in cuerpo["estados"]] == ["identificada", "formalizada", "medida", "optimizada"]
    assert [p["valor"] for p in cuerpo["periodicidades"]] == ["mensual", "trimestral", "semestral", "anual"]
    assert [t["valor"] for t in cuerpo["tipos_indicador"]] == ["institucional", "tecnico"]
