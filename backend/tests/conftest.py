import pytest


@pytest.fixture(autouse=True)
def _cache_limpio():
    from django.core.cache import cache

    cache.clear()


@pytest.fixture(autouse=True)
def _hasher_rapido(settings):
    # PBKDF2 es lento a propósito; en tests un hasher barato acelera la suite sin cambiar el comportamiento.
    settings.PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]


@pytest.fixture
def api_para():
    from rest_framework.test import APIClient

    def crear(usuario=None):
        cliente = APIClient()
        if usuario is not None:
            cliente.force_authenticate(user=usuario)
        return cliente

    return crear


@pytest.fixture
def user_factory(db):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    contador = {"n": 0}

    def crear(**kwargs):
        contador["n"] += 1
        kwargs.setdefault("username", f"usuario{contador['n']}")
        password = kwargs.pop("password", "clave-de-prueba-1")
        return User.objects.create_user(password=password, **kwargs)

    return crear


@pytest.fixture
def region(db):
    from catalog.models import Region

    return Region.objects.create(nombre="NEA")


@pytest.fixture
def facultad(region):
    from catalog.models import Facultad

    return Facultad.objects.create(nombre="Resistencia", region=region)


@pytest.fixture
def otra_facultad(db):
    from catalog.models import Facultad, Region

    centro = Region.objects.create(nombre="Centro")
    return Facultad.objects.create(nombre="Rafaela", region=centro)


@pytest.fixture
def practica(facultad):
    from catalog.models import Dimension, Practica

    return Practica.objects.create(
        facultad=facultad, nombre="Paneles solares", dimension=Dimension.AMBIENTAL
    )


@pytest.fixture
def indicador(practica):
    from indicators.models import Indicador, Periodicidad, TipoIndicador

    return Indicador.objects.create(
        practica=practica,
        nombre="Energía generada",
        formula="Suma mensual de kWh generados",
        unidad="kWh",
        periodicidad=Periodicidad.MENSUAL,
        tipo=TipoIndicador.INSTITUCIONAL,
    )


@pytest.fixture(autouse=True)
def _media_temporal(settings, tmp_path):
    settings.MEDIA_ROOT = tmp_path / "media"


@pytest.fixture
def escenario_simple(indicador, user_factory):
    """(medicion, usuario) mínimo para tests que no necesitan roles."""
    from decimal import Decimal

    from indicators.models import Medicion

    usuario = user_factory()
    medicion = Medicion.objects.create(
        indicador=indicador, periodo="2026-01", valor=Decimal("10"), cargado_por=usuario
    )
    return medicion, usuario


@pytest.fixture
def escenario(facultad, practica, indicador, user_factory):
    from decimal import Decimal
    from types import SimpleNamespace

    from accounts.models import Membership, Rol
    from indicators.models import Medicion

    responsable = user_factory(username="responsable")
    validador = user_factory(username="validador")
    Membership.objects.create(user=responsable, facultad=facultad, rol=Rol.RESPONSABLE)
    Membership.objects.create(user=validador, facultad=facultad, rol=Rol.VALIDADOR)
    medicion = Medicion.objects.create(
        indicador=indicador, periodo="2026-01", valor=Decimal("120.5"), cargado_por=responsable
    )
    return SimpleNamespace(
        facultad=facultad,
        practica=practica,
        indicador=indicador,
        medicion=medicion,
        responsable=responsable,
        validador=validador,
    )
