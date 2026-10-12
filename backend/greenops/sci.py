from dataclasses import dataclass

from .ops import UNIDAD_FUNCIONAL_OPS


@dataclass(frozen=True)
class Agregado:
    n: int
    cpu_ms: float
    wall_ms: float


def calcular_sci(agregado: Agregado, params) -> dict | None:
    """SCI = ((E x I) + M) / R, con R = n / 1000 unidades funcionales de 1.000 operaciones.

    E (kWh) se estima como tiempo de CPU x potencia; M prorratea las emisiones incorporadas
    según TE x (TS / EL) x (RS / TR). No es una medición de hardware.
    """
    if agregado.n == 0:
        return None
    potencia = float(params.potencia_cpu_w)
    intensidad = float(params.intensidad_carbono_g_kwh)
    te = float(params.te_g)
    el = float(params.el_horas)
    rs = float(params.rs)
    tr = float(params.tr)

    r_unidades = agregado.n / UNIDAD_FUNCIONAL_OPS
    e_kwh = (agregado.cpu_ms / 1000) * potencia / 3_600_000
    ts_horas = (agregado.wall_ms / 1000) / 3600
    m_g = te * (ts_horas / el) * (rs / tr)
    sci = (e_kwh * intensidad + m_g) / r_unidades

    return {
        "sci_g_por_1000_ops": round(sci, 6),
        "e_kwh": e_kwh,
        "m_g": m_g,
        "n_operaciones": agregado.n,
        "r_unidades": r_unidades,
        "cpu_ms_total": agregado.cpu_ms,
        "wall_ms_total": agregado.wall_ms,
    }
