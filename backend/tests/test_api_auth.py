import json

import pytest
from django.test import Client

from accounts.models import Membership, Rol

pytestmark = pytest.mark.django_db

SESION = "/api/auth/session/"
LOGIN = "/api/auth/login/"
LOGOUT = "/api/auth/logout/"


def credenciales(password="clave-de-prueba-1"):
    return json.dumps({"username": "ana", "password": password})


def test_sesion_anonima_entrega_la_cookie_csrf(client):
    respuesta = client.get(SESION)

    assert respuesta.status_code == 200
    assert respuesta.json() == {"authenticated": False, "membresias": []}
    assert "csrftoken" in respuesta.cookies


def test_login_exige_token_csrf(user_factory):
    user_factory(username="ana")
    cliente = Client(enforce_csrf_checks=True)
    cliente.get(SESION)

    respuesta = cliente.post(LOGIN, data=credenciales(), content_type="application/json")

    assert respuesta.status_code == 403


def test_login_con_token_csrf_devuelve_la_sesion(user_factory, facultad):
    ana = user_factory(username="ana")
    Membership.objects.create(user=ana, facultad=facultad, rol=Rol.RESPONSABLE)
    cliente = Client(enforce_csrf_checks=True)
    cliente.get(SESION)
    token = cliente.cookies["csrftoken"].value

    respuesta = cliente.post(
        LOGIN, data=credenciales(), content_type="application/json", HTTP_X_CSRFTOKEN=token
    )

    assert respuesta.status_code == 200
    cuerpo = respuesta.json()
    assert cuerpo["authenticated"] is True
    assert cuerpo["username"] == "ana"
    assert cuerpo["es_admin"] is False
    assert cuerpo["membresias"] == [
        {"facultad": facultad.id, "facultad_nombre": "Resistencia", "rol": "responsable"}
    ]


def test_login_con_credenciales_incorrectas_devuelve_400(client, user_factory):
    user_factory(username="ana")

    respuesta = client.post(LOGIN, data=credenciales("incorrecta"), content_type="application/json")

    assert respuesta.status_code == 400
    assert "incorrectos" in respuesta.json()["detail"]


@pytest.mark.parametrize("cuerpo", ["no es json", "[]", '"texto"'])
def test_login_con_cuerpo_invalido_devuelve_400(client, cuerpo):
    respuesta = client.post(LOGIN, data=cuerpo, content_type="application/json")

    assert respuesta.status_code == 400


def test_logout_cierra_la_sesion(client, user_factory):
    client.force_login(user_factory(username="ana"))
    assert client.get(SESION).json()["authenticated"] is True

    client.post(LOGOUT)

    assert client.get(SESION).json()["authenticated"] is False
