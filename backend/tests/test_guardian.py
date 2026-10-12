import pytest

from accounts.models import Membership, Rol
from catalog.models import Dimension, Practica

pytestmark = pytest.mark.django_db

PERMISO = "catalog.change_practica"


def test_el_responsable_recibe_el_permiso_sobre_las_practicas_existentes(escenario):
    assert escenario.responsable.has_perm(PERMISO, escenario.practica)


def test_un_validador_no_recibe_el_permiso(escenario):
    assert not escenario.validador.has_perm(PERMISO, escenario.practica)


def test_una_practica_nueva_hereda_el_permiso_de_los_responsables_de_su_facultad(escenario):
    nueva = Practica.objects.create(facultad=escenario.facultad, nombre="Nueva", dimension=Dimension.SOCIAL)

    assert escenario.responsable.has_perm(PERMISO, nueva)
    assert not escenario.validador.has_perm(PERMISO, nueva)


def test_al_borrar_la_membresia_se_retira_el_permiso(escenario):
    Membership.objects.get(user=escenario.responsable, rol=Rol.RESPONSABLE).delete()

    assert not escenario.responsable.has_perm(PERMISO, escenario.practica)


# Final review: cambiar rol o facultad de una membresía existente dejaría permisos de objeto desactualizados
def test_la_membresia_existente_no_se_edita_desde_el_admin(escenario):
    from django.contrib.admin.sites import AdminSite

    from accounts.admin import MembershipAdmin

    modelo_admin = MembershipAdmin(Membership, AdminSite())
    membresia = Membership.objects.get(user=escenario.responsable, rol=Rol.RESPONSABLE)

    assert {"user", "facultad", "rol"} <= set(modelo_admin.get_readonly_fields(None, membresia))
    assert not modelo_admin.get_readonly_fields(None, None)  # el alta sigue siendo libre


def test_un_responsable_de_otra_facultad_no_tiene_el_permiso(escenario, otra_facultad, user_factory):
    ajeno = user_factory()
    Membership.objects.create(user=ajeno, facultad=otra_facultad, rol=Rol.RESPONSABLE)

    assert not ajeno.has_perm(PERMISO, escenario.practica)


def test_el_administrador_tiene_el_permiso_siempre(escenario, user_factory):
    assert user_factory(is_superuser=True).has_perm(PERMISO, escenario.practica)
