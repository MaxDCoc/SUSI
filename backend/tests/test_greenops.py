from datetime import date
from decimal import Decimal

import pytest

from greenops.models import MuestraOperacion, ParametroSCI
from greenops.ops import OPS_NUCLEO, nombre_operacion
from greenops.sci import Agregado, calcular_sci

pytestmark = pytest.mark.django_db

SCI = "/api/green/sci/"
MUESTRAS = "/api/green/muestras/"
PARAMETROS = "/api/green/parametros/"


@pytest.fixture
def greenops_activo(settings):
    settings.GREENOPS_ENABLED = True


@pytest.fixture
def parametros(db):
    # Valores ficticios SOLO para tests (el seed real no inventa parámetros).
    return ParametroSCI.objects.create(
        potencia_cpu_w=Decimal("100"),
        intensidad_carbono_g_kwh=Decimal("200"),
        fuente_intensidad="Fuente ficticia de prueba",
        fecha_intensidad=date(2026, 1, 1),
        te_g=Decimal("100000"),
        el_horas=Decimal("10000"),
        rs=Decimal("1"),
        tr=Decimal("1"),
    )


def cargar_muestras(operacion, cantidad, cpu_ms=100.0, wall_ms=200.0):
    MuestraOperacion.objects.bulk_create(
        [
            MuestraOperacion(
                operacion=operacion, cpu_ms=cpu_ms, wall_ms=wall_ms, bytes_respuesta=500, n_consultas_sql=3
            )
            for _ in range(cantidad)
        ]
    )


# ---------- nombres de operación ----------


@pytest.mark.parametrize(
    "metodo,url_name,esperado",
    [
        ("GET", "practica-list", "practica.consultar"),
        ("POST", "practica-list", "practica.crear"),
        ("GET", "practica-detail", "practica.consultar"),
        ("PATCH", "practica-detail", "practica.actualizar"),
        ("POST", "medicion-validar", "medicion.validar"),
        ("GET", "dashboard-resumen", "dashboard.resumen"),
        ("GET", None, None),
    ],
)
def test_nombre_operacion(metodo, url_name, esperado):
    assert nombre_operacion(metodo, url_name) == esperado


def test_el_flujo_nucleo_son_tres_operaciones():
    assert OPS_NUCLEO == ("practica.crear", "practica.consultar", "medicion.validar")


# ---------- cálculo SCI ----------


def test_calcular_sci_con_un_ejemplo_resuelto_a_mano(parametros):
    # 10 operaciones con 100 ms de CPU y 200 ms de reloj cada una.
    # E = 1 s * 100 W / 3.6e6 = 2.7778e-5 kWh; E*I = 5.5556e-3 g
    # M = 100000 g * (2 s / 3600 / 10000 h) = 5.5556e-3 g
    # R = 10 / 1000 = 0.01 unidades funcionales -> SCI = (E*I + M) / R = 1.1111 g por 1000 ops
    resultado = calcular_sci(Agregado(n=10, cpu_ms=1000.0, wall_ms=2000.0), parametros)

    assert resultado["e_kwh"] == pytest.approx(2.7778e-5, rel=1e-3)
    assert resultado["m_g"] == pytest.approx(5.5556e-3, rel=1e-3)
    assert resultado["r_unidades"] == pytest.approx(0.01)
    assert resultado["sci_g_por_1000_ops"] == pytest.approx(1.1111, rel=1e-3)
    assert resultado["n_operaciones"] == 10


# Review Focus 4: sin muestras no hay división por cero
def test_calcular_sci_sin_muestras_devuelve_none(parametros):
    assert calcular_sci(Agregado(n=0, cpu_ms=0.0, wall_ms=0.0), parametros) is None


def test_la_version_de_los_parametros_se_asigna_sola(parametros):
    segundo = ParametroSCI.objects.create(
        potencia_cpu_w=Decimal("50"),
        intensidad_carbono_g_kwh=Decimal("100"),
        fuente_intensidad="Otra fuente ficticia",
        fecha_intensidad=date(2026, 2, 1),
        te_g=Decimal("1000"),
        el_horas=Decimal("100"),
        rs=Decimal("1"),
        tr=Decimal("1"),
    )

    assert (parametros.version, segundo.version) == (1, 2)


# ---------- middleware ----------


def test_el_middleware_registra_una_muestra_por_operacion_de_la_api(greenops_activo, client, user_factory, escenario):
    client.force_login(escenario.responsable)

    client.get("/api/practicas/")

    muestra = MuestraOperacion.objects.get()
    assert muestra.operacion == "practica.consultar"
    assert muestra.n_consultas_sql >= 1
    assert muestra.bytes_respuesta > 0
    assert muestra.cpu_ms >= 0 and muestra.wall_ms > 0


def test_el_middleware_no_se_mide_a_si_mismo_ni_mide_lo_que_no_es_api(greenops_activo, client, escenario):
    client.force_login(escenario.responsable)

    client.get(SCI)
    client.get(MUESTRAS)
    client.get("/health/")
    client.get("/api/ruta-inexistente/")

    assert MuestraOperacion.objects.count() == 0


def test_con_greenops_apagado_no_se_guarda_nada(client, escenario):
    client.force_login(escenario.responsable)

    client.get("/api/practicas/")

    assert MuestraOperacion.objects.count() == 0


# ---------- API ----------


def test_sci_sin_parametros_explica_que_faltan(api_para, user_factory):
    cuerpo = api_para(user_factory()).get(SCI).json()

    assert cuerpo["sci"] is None and cuerpo["parametros"] is None
    assert "parámetros" in cuerpo["motivo"]
    assert cuerpo["estimacion"] is True


def test_sci_con_parametros_pero_sin_muestras(api_para, user_factory, parametros):
    cuerpo = api_para(user_factory()).get(SCI).json()

    assert cuerpo["sci"] is None
    assert "operaciones" in cuerpo["motivo"]
    assert cuerpo["parametros"]["version"] == 1


def test_sci_usa_solo_las_operaciones_del_flujo_nucleo(api_para, user_factory, parametros):
    cargar_muestras("practica.crear", 4)
    cargar_muestras("practica.consultar", 3)
    cargar_muestras("medicion.validar", 3)
    cargar_muestras("dashboard.resumen", 50, cpu_ms=9999.0, wall_ms=9999.0)  # no es flujo núcleo

    cuerpo = api_para(user_factory()).get(SCI).json()

    assert cuerpo["unidad_funcional"]["ops"] == 1000
    assert cuerpo["sci"]["n_operaciones"] == 10
    assert cuerpo["sci"]["sci_g_por_1000_ops"] == pytest.approx(1.1111, rel=1e-3)
    assert "estimación" in cuerpo["aviso"].lower()


def test_muestras_resume_por_operacion(api_para, user_factory):
    cargar_muestras("practica.consultar", 4, cpu_ms=10.0)

    cuerpo = api_para(user_factory()).get(MUESTRAS).json()

    assert cuerpo["total"] == 4
    assert cuerpo["operaciones"] == [
        {
            "operacion": "practica.consultar",
            "n": 4,
            "cpu_ms_prom": 10.0,
            "wall_ms_prom": 200.0,
            "bytes_prom": 500.0,
            "consultas_prom": 3.0,
        }
    ]


def test_solo_el_administrador_carga_parametros(api_para, user_factory):
    datos = {
        "potencia_cpu_w": "65",
        "intensidad_carbono_g_kwh": "300",
        "fuente_intensidad": "Fuente de prueba",
        "fecha_intensidad": "2026-01-01",
        "te_g": "50000",
        "el_horas": "20000",
        "rs": "1",
        "tr": "4",
    }

    assert api_para(user_factory()).post(PARAMETROS, datos, format="json").status_code == 403

    admin = api_para(user_factory(is_superuser=True))
    creado = admin.post(PARAMETROS, datos, format="json")
    assert creado.status_code == 201 and creado.json()["version"] == 1
    assert admin.post(PARAMETROS, datos, format="json").json()["version"] == 2


def test_los_parametros_invalidos_dan_400(api_para, user_factory):
    datos = {
        "potencia_cpu_w": "65",
        "intensidad_carbono_g_kwh": "300",
        "fuente_intensidad": "Fuente de prueba",
        "fecha_intensidad": "2026-01-01",
        "te_g": "50000",
        "el_horas": "0",  # división por cero en M
        "rs": "1",
        "tr": "0",
    }

    respuesta = api_para(user_factory(is_superuser=True)).post(PARAMETROS, datos, format="json")

    assert respuesta.status_code == 400
    assert "el_horas" in respuesta.json() and "tr" in respuesta.json()
