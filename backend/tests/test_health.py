import pytest
from django.db import OperationalError


def test_health_responde_ok(client):
    # Sin la fixture `db`: pytest-django falla si esta ruta toca la base. El monitor que mantiene despierta
    # la app le pega seguido y no debe despertar (ni gastar horas de) la base de datos.
    respuesta = client.get("/health/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok"}


@pytest.mark.django_db
def test_health_db_consulta_la_base_y_responde_ok(client):
    respuesta = client.get("/health/db/")

    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "base": "ok"}


def test_health_db_responde_503_sin_detalles_si_la_base_falla(client, monkeypatch):
    class BaseCaida:
        def cursor(self):
            raise OperationalError("password authentication failed for user susi")

    monkeypatch.setattr("susi.views.connection", BaseCaida())

    respuesta = client.get("/health/db/")

    assert respuesta.status_code == 503
    assert respuesta.json() == {"status": "error", "base": "no disponible"}
