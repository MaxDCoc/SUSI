import re

import pytest
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.core.management.base import CommandError

from accounts.models import Membership, Rol
from catalog.models import ESTADOS_ORDEN, ODS, Estado, Facultad, Origen, Practica, Region
from evidence.models import Evidencia
from greenops.models import ParametroSCI
from indicators.models import EstadoMedicion, Indicador, Medicion
from workflow.services import requisito_faltante

pytestmark = pytest.mark.django_db

CLAVE = "clave-demo-de-prueba-9"
User = get_user_model()


@pytest.fixture
def con_clave(monkeypatch):
    monkeypatch.setenv("SUSI_DEMO_PASSWORD", CLAVE)


# Review Focus 5: seed inseguro
def test_sin_clave_falla_y_no_crea_nada(monkeypatch):
    monkeypatch.delenv("SUSI_DEMO_PASSWORD", raising=False)

    with pytest.raises(CommandError, match="SUSI_DEMO_PASSWORD"):
        call_command("seed_demo")

    assert User.objects.count() == 0
    assert Facultad.objects.count() == 0


def test_solo_catalogos_no_necesita_clave_ni_crea_usuarios_ni_practicas(monkeypatch):
    monkeypatch.delenv("SUSI_DEMO_PASSWORD", raising=False)

    call_command("seed_demo", "--solo-catalogos")

    assert Facultad.objects.count() == 31
    assert User.objects.count() == 0 and Practica.objects.count() == 0


def test_carga_las_30_facultades_regionales_el_rectorado_y_los_ods(con_clave):
    call_command("seed_demo")

    assert Region.objects.count() == 7
    assert Facultad.objects.count() == 31
    assert Facultad.objects.filter(es_nivel_central=False).count() == 30
    assert list(Facultad.objects.filter(es_nivel_central=True).values_list("nombre", flat=True)) == ["Rectorado"]
    assert ODS.objects.count() == 17
    por_region = {r.nombre: r.facultades.count() for r in Region.objects.all()}
    assert por_region == {
        "NEA": 1,
        "NOA": 2,
        "Cuyo": 2,
        "Centro": 11,
        "Buenos Aires": 10,
        "Patagonia": 4,
        "Nivel Central": 1,
    }


def test_crea_los_usuarios_de_demo_con_sus_roles(con_clave):
    call_command("seed_demo")

    admin = User.objects.get(username="admin.demo")
    assert admin.is_superuser and admin.check_password(CLAVE)
    responsable = User.objects.get(username="responsable.demo")
    validador = User.objects.get(username="validador.demo")
    assert responsable.check_password(CLAVE) and not responsable.is_superuser
    assert Membership.objects.filter(user=responsable, rol=Rol.RESPONSABLE).count() == 5
    assert Membership.objects.filter(user=validador, rol=Rol.VALIDADOR).count() == 5
    assert not Membership.objects.filter(user=responsable, rol=Rol.VALIDADOR).exists()


def test_es_idempotente(con_clave):
    call_command("seed_demo")
    antes = (Facultad.objects.count(), Practica.objects.count(), Medicion.objects.count(), User.objects.count())

    call_command("seed_demo")

    assert (Facultad.objects.count(), Practica.objects.count(), Medicion.objects.count(), User.objects.count()) == antes
    assert antes[3] == 3


def test_todas_las_practicas_son_ilustrativas(con_clave):
    call_command("seed_demo")

    assert Practica.objects.count() == 9
    assert set(Practica.objects.values_list("origen", flat=True)) == {Origen.ILUSTRATIVA}
    assert all(p.proposito.startswith("Datos ilustrativos") for p in Practica.objects.all())


def test_los_estados_sembrados_cumplen_las_reglas_del_workflow(con_clave):
    call_command("seed_demo")

    for practica in Practica.objects.all():
        alcanzados = ESTADOS_ORDEN[1 : ESTADOS_ORDEN.index(practica.estado) + 1]
        for destino in alcanzados:
            assert requisito_faltante(practica, destino) is None, f"{practica} no cumple {destino}"


def test_queda_una_medicion_enviada_lista_para_la_demo_en_vivo(con_clave):
    call_command("seed_demo")

    enviada = Medicion.objects.get(estado=EstadoMedicion.ENVIADA)
    practica = enviada.indicador.practica
    assert enviada.cargado_por.username == "responsable.demo"
    assert practica.estado == Estado.FORMALIZADA
    assert requisito_faltante(practica, Estado.MEDIDA) is not None  # falta validarla


def test_no_se_inventan_parametros_sci(con_clave):
    call_command("seed_demo")

    assert ParametroSCI.objects.count() == 0


def test_no_hay_datos_personales_en_los_textos_sembrados(con_clave):
    call_command("seed_demo")

    textos = []
    for p in Practica.objects.all():
        textos += [p.nombre, p.proposito, p.alcance, p.actividades, p.frecuencia]
    for i in Indicador.objects.all():
        textos += [i.nombre, i.formula, i.fuente, i.referencia_estandar]
    for m in Medicion.objects.all():
        textos += [m.comentario_validacion]
    for e in Evidencia.objects.all():
        textos += [e.descripcion, e.url]

    for texto in textos:
        assert "@" not in texto, texto
        assert not re.search(r"\d{8,}", texto), texto
