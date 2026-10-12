from django.db.models import Count

from catalog.models import ESTADOS_ORDEN, Dimension, Facultad, Practica
from indicators.models import EstadoMedicion

ESTADOS = [estado.value for estado in ESTADOS_ORDEN]
ETIQUETAS_DIMENSION = dict(Dimension.choices)


def practicas_filtradas(filtros: dict):
    qs = Practica.objects.all()
    if filtros.get("facultad"):
        qs = qs.filter(facultad_id=filtros["facultad"])
    if filtros.get("region"):
        qs = qs.filter(facultad__region_id=filtros["region"])
    if filtros.get("dimension"):
        qs = qs.filter(dimension=filtros["dimension"])
    if filtros.get("ods"):
        qs = qs.filter(ods__numero=filtros["ods"])
    return qs


def porcentaje(parte: int, total: int) -> float:
    return round(100 * parte / total, 1) if total else 0.0


def embudo(qs) -> dict:
    conteos = dict(qs.order_by().values_list("estado").annotate(n=Count("id")))
    return {estado: conteos.get(estado, 0) for estado in ESTADOS}


def _agrupar(qs, campo_clave: str, campos_extra: tuple, etiqueta) -> list:
    filas = qs.order_by().values(campo_clave, *campos_extra, "estado").annotate(n=Count("id"))
    grupos: dict = {}
    for fila in filas:
        clave = fila[campo_clave]
        grupo = grupos.setdefault(
            clave, {"clave": clave, "etiqueta": etiqueta(fila), "total": 0, **{e: 0 for e in ESTADOS}}
        )
        grupo[fila["estado"]] += fila["n"]
        grupo["total"] += fila["n"]
    return sorted(grupos.values(), key=lambda g: (-g["total"], str(g["etiqueta"])))


def _kpi(cantidad: int, total: int) -> dict:
    return {"cantidad": cantidad, "porcentaje": porcentaje(cantidad, total)}


def resumen(filtros: dict) -> dict:
    qs = practicas_filtradas(filtros)
    total = qs.count()
    con_responsable = qs.exclude(responsable__isnull=True).count()
    con_indicador = qs.filter(indicadores__isnull=False).distinct().count()
    con_evidencia_validada = (
        qs.filter(
            indicadores__mediciones__estado=EstadoMedicion.VALIDADA,
            indicadores__mediciones__evidencias__isnull=False,
        )
        .distinct()
        .count()
    )

    facultades = Facultad.objects.filter(es_nivel_central=False)
    if filtros.get("facultad"):
        facultades = facultades.filter(pk=filtros["facultad"])
    if filtros.get("region"):
        facultades = facultades.filter(region_id=filtros["region"])
    facultades_total = facultades.count()
    con_practicas = (
        qs.filter(facultad__es_nivel_central=False).order_by().values("facultad_id").distinct().count()
    )

    return {
        "total_practicas": total,
        "kpis": {
            "con_responsable": _kpi(con_responsable, total),
            "con_indicador": _kpi(con_indicador, total),
            "con_evidencia_validada": _kpi(con_evidencia_validada, total),
        },
        "cobertura": {
            "facultades_con_practicas": con_practicas,
            "facultades_total": facultades_total,
            "porcentaje": porcentaje(con_practicas, facultades_total),
        },
        "embudo": embudo(qs),
        "por_facultad": _agrupar(qs, "facultad_id", ("facultad__nombre",), lambda f: f["facultad__nombre"]),
        "por_region": _agrupar(
            qs, "facultad__region_id", ("facultad__region__nombre",), lambda f: f["facultad__region__nombre"]
        ),
        "por_dimension": _agrupar(qs, "dimension", (), lambda f: ETIQUETAS_DIMENSION[f["dimension"]]),
        "por_ods": _agrupar(
            qs.filter(ods__isnull=False),
            "ods__numero",
            ("ods__nombre",),
            lambda f: f"ODS {f['ods__numero']}: {f['ods__nombre']}",
        ),
    }
