import pytest

pytestmark = pytest.mark.django_db


def test_el_spa_se_sirve_en_las_rutas_del_cliente(client, settings, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html><title>SUSI</title>", encoding="utf-8")
    settings.FRONTEND_DIST = tmp_path

    for ruta in ("/", "/practicas/3", "/tablero"):
        respuesta = client.get(ruta)
        assert respuesta.status_code == 200, ruta
        assert b"<title>SUSI</title>" in respuesta.content
        assert respuesta["Content-Type"].startswith("text/html")


def test_el_spa_no_tapa_la_api_ni_el_admin_ni_el_health(client, settings, tmp_path):
    (tmp_path / "index.html").write_text("<!doctype html>", encoding="utf-8")
    settings.FRONTEND_DIST = tmp_path

    assert client.get("/api/ruta-que-no-existe/").status_code == 404
    assert client.get("/admin/").status_code == 302  # redirige al login del admin
    assert client.get("/health/").json() == {"status": "ok"}


def test_sin_build_del_frontend_da_404_con_la_indicacion(client, settings, tmp_path):
    settings.FRONTEND_DIST = tmp_path / "no-existe"

    respuesta = client.get("/practicas")

    assert respuesta.status_code == 404
