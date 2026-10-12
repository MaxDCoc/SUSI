from django.db.models import Avg, Count, Sum
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.scope import es_admin

from .models import MuestraOperacion, ParametroSCI
from .ops import OPS_NUCLEO, UNIDAD_FUNCIONAL_OPS
from .sci import Agregado, calcular_sci
from .serializers import ParametroSCISerializer

AVISO = (
    "Estimación basada en el tiempo de CPU medido y en supuestos configurables; "
    "no es una medición de hardware."
)


class SCIView(APIView):
    def get(self, request):
        respuesta = {
            "unidad_funcional": {
                "ops": UNIDAD_FUNCIONAL_OPS,
                "descripcion": "1.000 operaciones del flujo núcleo",
                "operaciones": list(OPS_NUCLEO),
            },
            "estimacion": True,
            "aviso": AVISO,
            "parametros": None,
            "sci": None,
            "motivo": None,
        }
        parametros = ParametroSCI.objects.order_by("-version").first()
        if parametros is None:
            respuesta["motivo"] = (
                "No hay parámetros SCI cargados (potencia, intensidad de carbono y emisiones incorporadas)."
            )
            return Response(respuesta)

        respuesta["parametros"] = ParametroSCISerializer(parametros).data
        datos = MuestraOperacion.objects.filter(operacion__in=OPS_NUCLEO).aggregate(
            n=Count("id"), cpu=Sum("cpu_ms"), wall=Sum("wall_ms")
        )
        agregado = Agregado(n=datos["n"], cpu_ms=datos["cpu"] or 0.0, wall_ms=datos["wall"] or 0.0)
        resultado = calcular_sci(agregado, parametros)
        if resultado is None:
            respuesta["motivo"] = "Todavía no hay operaciones del flujo núcleo medidas."
        else:
            respuesta["sci"] = resultado
        return Response(respuesta)


class MuestrasView(APIView):
    def get(self, request):
        filas = (
            MuestraOperacion.objects.order_by()
            .values("operacion")
            .annotate(
                n=Count("id"),
                cpu_ms_prom=Avg("cpu_ms"),
                wall_ms_prom=Avg("wall_ms"),
                bytes_prom=Avg("bytes_respuesta"),
                consultas_prom=Avg("n_consultas_sql"),
            )
            .order_by("operacion")
        )
        operaciones = [
            {
                "operacion": f["operacion"],
                "n": f["n"],
                "cpu_ms_prom": round(f["cpu_ms_prom"], 3),
                "wall_ms_prom": round(f["wall_ms_prom"], 3),
                "bytes_prom": round(f["bytes_prom"], 1),
                "consultas_prom": round(f["consultas_prom"], 2),
            }
            for f in filas
        ]
        return Response({"total": sum(o["n"] for o in operaciones), "operaciones": operaciones})


class ParametrosView(APIView):
    def get(self, request):
        return Response(ParametroSCISerializer(ParametroSCI.objects.order_by("-version"), many=True).data)

    def post(self, request):
        if not es_admin(request.user):
            raise PermissionDenied("Solo el Administrador puede cargar parámetros SCI.")
        serializer = ParametroSCISerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
