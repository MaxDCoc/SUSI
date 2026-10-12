import pytest
from django.contrib.auth.models import AnonymousUser
from django.db import IntegrityError, transaction
from rest_framework.exceptions import PermissionDenied

from accounts.models import Membership, Rol
from accounts.scope import es_admin, exigir_rol, tiene_rol

pytestmark = pytest.mark.django_db


def test_responsable_solo_tiene_rol_en_su_facultad(user_factory, facultad, otra_facultad):
    usuario = user_factory()
    Membership.objects.create(user=usuario, facultad=facultad, rol=Rol.RESPONSABLE)

    assert tiene_rol(usuario, facultad.id, Rol.RESPONSABLE)
    assert not tiene_rol(usuario, otra_facultad.id, Rol.RESPONSABLE)
    assert not tiene_rol(usuario, facultad.id, Rol.VALIDADOR)


def test_administrador_tiene_todos_los_roles(user_factory, facultad):
    admin = user_factory(is_superuser=True)

    assert es_admin(admin)
    assert tiene_rol(admin, facultad.id, Rol.VALIDADOR)
    assert tiene_rol(admin, facultad.id, Rol.RESPONSABLE)


def test_anonimo_no_tiene_roles(facultad):
    anonimo = AnonymousUser()

    assert not es_admin(anonimo)
    assert not tiene_rol(anonimo, facultad.id, Rol.RESPONSABLE)


def test_exigir_rol_levanta_403_si_falta_la_membresia(user_factory, facultad):
    with pytest.raises(PermissionDenied):
        exigir_rol(user_factory(), facultad.id, Rol.RESPONSABLE)


def test_exigir_rol_no_levanta_si_corresponde(user_factory, facultad):
    usuario = user_factory()
    Membership.objects.create(user=usuario, facultad=facultad, rol=Rol.VALIDADOR)

    exigir_rol(usuario, facultad.id, Rol.VALIDADOR)


def test_membresia_duplicada_no_se_permite(user_factory, facultad):
    usuario = user_factory()
    Membership.objects.create(user=usuario, facultad=facultad, rol=Rol.RESPONSABLE)

    with pytest.raises(IntegrityError), transaction.atomic():
        Membership.objects.create(user=usuario, facultad=facultad, rol=Rol.RESPONSABLE)
