import logging
import time

from django.conf import settings
from django.db import connection

from .models import MuestraOperacion
from .ops import nombre_operacion

logger = logging.getLogger(__name__)


class _ContadorSQL:
    def __init__(self):
        self.consultas = 0

    def __call__(self, execute, sql, params, many, context):
        self.consultas += 1
        return execute(sql, params, many, context)


class GreenOpsMiddleware:
    """Registra CPU, tiempo, bytes y consultas SQL de cada operación de la API."""

    def __init__(self, get_response):
        self.get_response = get_response

    @staticmethod
    def _medible(path: str) -> bool:
        return path.startswith("/api/") and not path.startswith("/api/green/")

    def __call__(self, request):
        if not settings.GREENOPS_ENABLED or not self._medible(request.path):
            return self.get_response(request)

        contador = _ContadorSQL()
        cpu_inicio = time.thread_time()
        reloj_inicio = time.perf_counter()
        with connection.execute_wrapper(contador):
            response = self.get_response(request)
        cpu_ms = (time.thread_time() - cpu_inicio) * 1000
        wall_ms = (time.perf_counter() - reloj_inicio) * 1000

        self._registrar(request, response, cpu_ms, wall_ms, contador.consultas)
        return response

    @staticmethod
    def _registrar(request, response, cpu_ms, wall_ms, consultas):
        coincidencia = getattr(request, "resolver_match", None)
        operacion = nombre_operacion(request.method, coincidencia.url_name if coincidencia else None)
        if operacion is None:
            return
        tamano = int(response.get("Content-Length", 0)) if response.streaming else len(response.content)
        try:
            MuestraOperacion.objects.create(
                operacion=operacion,
                cpu_ms=cpu_ms,
                wall_ms=wall_ms,
                bytes_respuesta=tamano,
                n_consultas_sql=consultas,
            )
        except Exception:  # la medición nunca debe romper una request
            logger.exception("No se pudo registrar la muestra de la operación %s", operacion)
