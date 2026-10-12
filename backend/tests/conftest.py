import pytest


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
